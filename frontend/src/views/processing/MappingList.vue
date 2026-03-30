<template>
  <div class="mapping-list">
    <div class="header-actions">
      <h2 class="page-title">数据映射配置</h2>
      <a-button type="primary" @click="$router.push('/processing/mappings/create')">
        <template #icon><PlusOutlined /></template>
        新建配置
      </a-button>
    </div>

    <a-card class="table-card">
      <a-form layout="inline" class="search-form">
        <a-form-item label="配置名称">
          <a-input v-model:value="searchForm.name" placeholder="请输入名称" allow-clear />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="searchForm.status" placeholder="请选择状态" style="width: 120px" allow-clear>
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="active">已激活</a-select-option>
            <a-select-option value="disabled">已禁用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSearch">查询</a-button>
          <a-button style="margin-left: 8px" @click="handleReset">重置</a-button>
        </a-form-item>
      </a-form>

      <a-table
        :columns="columns"
        :data-source="mappings"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ record.status_display }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="$router.push(`/processing/mappings/${record.id}`)">
                编辑
              </a-button>
              <a-divider type="vertical" />
              <a-dropdown>
                <a class="ant-dropdown-link" @click.prevent>
                  更多 <DownOutlined />
                </a>
                <template #overlay>
                  <a-menu>
                    <a-menu-item v-if="record.status !== 'active'" @click="handleActivate(record)">
                      激活配置
                    </a-menu-item>
                    <a-menu-item v-if="record.status === 'active'" @click="handleDisable(record)">
                      禁用配置
                    </a-menu-item>
                    <a-menu-item @click="handleCreateTask(record)">
                      创建任务
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item danger @click="handleDelete(record)">
                      删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
          <template v-else>
            {{ record[column.dataIndex] }}
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建任务弹窗 -->
    <a-modal
      v-model:open="taskModalVisible"
      title="创建处理任务"
      @ok="handleTaskSubmit"
      :confirmLoading="taskSubmitLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="任务名称" required>
          <a-input v-model:value="taskForm.name" placeholder="请输入任务名称" />
        </a-form-item>
        <a-form-item label="映射配置">
          <a-input :value="taskForm.mappingName" disabled />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, DownOutlined } from '@ant-design/icons-vue'
import { getMappings, deleteMapping, activateMapping, disableMapping, createTask } from '@/api/processing'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const mappings = ref([])

const searchForm = reactive({
  name: '',
  status: undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true
})

const columns = [
  { title: '配置名称', dataIndex: 'name', key: 'name' },
  { title: '源文件', dataIndex: 'source_file_name', key: 'source_file' },
  { title: '目标模板', dataIndex: 'target_template_name', key: 'target_template' },
  { title: '包含任务', dataIndex: 'task_count', key: 'task_count', align: 'center' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 180 },
  { title: '操作', key: 'action', width: 180, fixed: 'right' }
]

function getStatusColor(status: string) {
  const map: Record<string, string> = {
    draft: 'default',
    active: 'success',
    disabled: 'error'
  }
  return map[status]
}

async function fetchMappings() {
  loading.value = true
  try {
    const res = await getMappings({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchForm.name,
      status: searchForm.status
    })
    const data = res.data?.data || res.data
    mappings.value = data.results || []
    pagination.total = data.pagination?.total || data.count || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchMappings()
}

function handleSearch() {
  pagination.current = 1
  fetchMappings()
}

function handleReset() {
  searchForm.name = ''
  searchForm.status = undefined
  handleSearch()
}

async function handleActivate(record: any) {
  try {
    await activateMapping(record.id)
    message.success('配置已激活')
    fetchMappings()
  } catch (error) {
    // Error handled by interceptor
  }
}

async function handleDisable(record: any) {
  try {
    await disableMapping(record.id)
    message.success('配置已禁用')
    fetchMappings()
  } catch (error) {
    // Error handled by interceptor
  }
}

function handleDelete(record: any) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除配置"${record.name}"吗？`,
    okType: 'danger',
    onOk: async () => {
      try {
        await deleteMapping(record.id)
        message.success('删除成功')
        fetchMappings()
      } catch (error) {
        // Error handled by interceptor
      }
    }
  })
}

// 任务创建相关
const taskModalVisible = ref(false)
const taskSubmitLoading = ref(false)
const taskForm = reactive({
  name: '',
  mappingId: 0,
  mappingName: ''
})

function handleCreateTask(record: any) {
  if (record.status !== 'active') {
    message.warning('只有已激活的配置才能创建任务')
    return
  }
  taskForm.mappingId = record.id
  taskForm.mappingName = record.name
  taskForm.name = `${record.name}-任务-${new Date().toISOString().slice(0, 10)}`
  taskModalVisible.value = true
}

async function handleTaskSubmit() {
  if (!taskForm.name) {
    message.warning('请输入任务名称')
    return
  }
  
  taskSubmitLoading.value = true
  try {
    await createTask({
      name: taskForm.name,
      mapping: taskForm.mappingId
    })
    message.success('任务创建成功')
    taskModalVisible.value = false
    router.push('/processing/tasks')
  } catch (error) {
    console.error(error)
  } finally {
    taskSubmitLoading.value = false
  }
}

onMounted(() => {
  fetchMappings()
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

.search-form {
  margin-bottom: 24px;
}
</style>
