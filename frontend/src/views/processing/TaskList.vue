<template>
  <div class="task-list">
    <div class="header-actions">
      <h2 class="page-title">处理任务</h2>
    </div>

    <!-- 搜索区域 -->
    <a-card class="search-card" :bordered="false">
      <a-form layout="inline" :model="searchForm">
        <a-form-item label="任务名称">
          <a-input v-model:value="searchForm.name" placeholder="请输入任务名称" allow-clear />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="searchForm.status" placeholder="请选择状态" allow-clear style="width: 120px">
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="pending">待执行</a-select-option>
            <a-select-option value="running">执行中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
            <a-select-option value="failed">失败</a-select-option>
            <a-select-option value="cancelled">已取消</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <SearchOutlined /> 查询
            </a-button>
            <a-button @click="handleReset">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 表格区域 -->
    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="tasks"
        :loading="loading"
        :pagination="pagination"
        :expanded-row-keys="expandedRowKeys"
        @change="handleTableChange"
        @expand="handleExpandRow"
        row-key="id"
      >
        <template #expandedRowRender="{ record }">
          <SheetResultsPanel
            :task-id="record.id"
            :task-status="record.status"
            :refresh-key="sheetResultRefreshKey[record.id] || 0"
          />
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ record.status_display }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'progress'">
            <div>
              <a-progress 
                :percent="record.progress" 
                :status="getProgressStatus(record.status)"
                size="small"
              />
              <span v-if="record.status === 'running' || record.total_rows > 0" class="progress-detail">
                {{ record.processed_rows }} / {{ record.total_rows }} 行
              </span>
            </div>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button 
                v-if="record.status === 'pending' || record.status === 'failed'" 
                type="link" 
                size="small" 
                @click="handleExecute(record)"
              >
                <PlayCircleOutlined /> 执行
              </a-button>
              <a-button 
                v-if="record.status === 'pending'" 
                type="link" 
                size="small" 
                @click="handleCancel(record)"
              >
                取消
              </a-button>
              <a-popconfirm
                v-if="record.status === 'running'"
                title="确定要终止这个正在运行的任务吗？"
                @confirm="handleTerminate(record)"
              >
                <a-button type="link" danger size="small">
                  <StopOutlined /> 终止
                </a-button>
              </a-popconfirm>
              <a-button 
                v-if="record.status === 'completed' && record.result_file" 
                type="link" 
                size="small" 
                @click="handleDownload(record)"
              >
                <DownloadOutlined /> 下载
              </a-button>
              <a-popconfirm
                title="确定要删除这个任务吗？"
                @confirm="handleDelete(record)"
              >
                <a-button type="link" danger size="small">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
          <template v-else>
            {{ record[column.dataIndex] }}
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { message } from 'ant-design-vue'
import { 
  SearchOutlined, 
  PlayCircleOutlined,
  DownloadOutlined,
  StopOutlined
} from '@ant-design/icons-vue'
import { 
  getTasks, 
  getTask,
  executeTask, 
  cancelTask, 
  terminateTask,
  deleteTask,
  downloadTaskResult,
  type ProcessingTask 
} from '@/api/processing'
import SheetResultsPanel from '@/components/processing/SheetResultsPanel.vue'

const loading = ref(false)
const tasks = ref<ProcessingTask[]>([])

// Req 16.1–16.4: track expanded rows + refresh key per task for polling
const expandedRowKeys = ref<number[]>([])
const sheetResultRefreshKey = reactive<Record<number, number>>({})

function handleExpandRow(expanded: boolean, record: ProcessingTask) {
  if (expanded) {
    if (!expandedRowKeys.value.includes(record.id)) {
      expandedRowKeys.value.push(record.id)
    }
    // Trigger initial load by bumping the refresh key
    sheetResultRefreshKey[record.id] = (sheetResultRefreshKey[record.id] || 0) + 1
  } else {
    expandedRowKeys.value = expandedRowKeys.value.filter(k => k !== record.id)
  }
}

let pollingTimer: ReturnType<typeof setInterval> | null = null
const POLLING_INTERVAL = 3000

function hasActiveTasks(): boolean {
  return tasks.value.some(t => t.status === 'running' || t.status === 'pending')
}

function startPolling() {
  stopPolling()
  if (!hasActiveTasks()) return
  pollingTimer = setInterval(async () => {
    const activeTasks = tasks.value.filter(t => t.status === 'running' || t.status === 'pending')
    if (activeTasks.length === 0) {
      stopPolling()
      return
    }
    try {
      const updates = await Promise.all(activeTasks.map(t => getTask(t.id)))
      for (const res of updates) {
        const updated = res.data?.data || res.data
        const idx = tasks.value.findIndex(t => t.id === updated.id)
        if (idx !== -1) {
          tasks.value[idx] = updated
        }
        // Req 16.3: if this task is expanded and still active,
        // bump its refresh key so the child panel re-fetches.
        if (
          expandedRowKeys.value.includes(updated.id) &&
          (updated.status === 'running' || updated.status === 'pending')
        ) {
          sheetResultRefreshKey[updated.id] = (sheetResultRefreshKey[updated.id] || 0) + 1
        }
      }
      // Req 16.4: If no more active tasks, stop polling (refresh keys stop changing → children stay at terminal state)
      if (!hasActiveTasks()) {
        stopPolling()
      }
    } catch {
      // Silently ignore polling errors
    }
  }, POLLING_INTERVAL)
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}
const searchForm = reactive({
  name: '',
  status: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true
})

const columns = [
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '关联配置', dataIndex: 'mapping_name', key: 'mapping_name' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '进度', key: 'progress', width: 180 },
  { title: '成功/失败', key: 'result', width: 120 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' }
]

function getStatusColor(status: string) {
  const map: Record<string, string> = {
    pending: 'default',
    running: 'processing',
    completed: 'success',
    failed: 'error',
    cancelled: 'warning'
  }
  return map[status] || 'default'
}

function getProgressStatus(status: string) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  if (status === 'running') return 'active'
  return 'normal'
}

async function fetchTasks() {
  loading.value = true
  try {
    const res = await getTasks({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchForm.name,
      status: searchForm.status
    })
    const data = res.data?.data || res.data
    tasks.value = data.results || []
    pagination.total = data.pagination?.total || data.count || 0
    // Start polling if there are running/pending tasks
    if (hasActiveTasks()) {
      startPolling()
    }
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchTasks()
}

function handleSearch() {
  pagination.current = 1
  fetchTasks()
}

function handleReset() {
  searchForm.name = ''
  searchForm.status = ''
  pagination.current = 1
  fetchTasks()
}

async function handleExecute(record: ProcessingTask) {
  try {
    await executeTask(record.id)
    message.success('任务开始执行')
    await fetchTasks()
    startPolling()
  } catch (error) {
    message.error('执行失败')
  }
}

async function handleCancel(record: ProcessingTask) {
  try {
    await cancelTask(record.id)
    message.success('任务已取消')
    fetchTasks()
  } catch (error) {
    message.error('取消失败')
  }
}

async function handleTerminate(record: ProcessingTask) {
  try {
    await terminateTask(record.id)
    message.success('任务已终止')
    fetchTasks()
  } catch (error) {
    message.error('终止失败')
  }
}

async function handleDownload(record: ProcessingTask) {
  try {
    const response = await downloadTaskResult(record.id)
    const blob = new Blob([response.data])
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = `${record.name}_result.xlsx`
    link.click()
    window.URL.revokeObjectURL(link.href)
    message.success('下载开始')
  } catch (error) {
    message.error('下载失败')
  }
}

async function handleDelete(record: ProcessingTask) {
  try {
    await deleteTask(record.id)
    message.success('删除成功')
    fetchTasks()
  } catch (error) {
    message.error('删除失败')
  }
}

onMounted(() => {
  fetchTasks()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  font-family: 'Fira Code', monospace;
  color: var(--color-text);
}

.search-card {
  margin-bottom: 16px;
}

.progress-detail {
  display: block;
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}
</style>
