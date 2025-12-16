<template>
  <div class="logs-page">
    <div class="header-actions">
      <h2 class="page-title">操作日志</h2>
      <div class="actions">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索用户、路径或IP..."
          style="width: 250px"
          @search="handleSearch"
        />
        <a-button @click="fetchLogs">
          <ReloadOutlined /> 刷新
        </a-button>
      </div>
    </div>

    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="logList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'method'">
            <a-tag :color="getMethodColor(record.method)">
              {{ record.method }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'response_code'">
             <a-tag :color="record.response_code < 400 ? 'success' : 'error'">
              {{ record.response_code }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'params'">
            <a-typography-paragraph
              :content="record.params || '-'"
              :ellipsis="{ rows: 1, expandable: true, symbol: '展开' }"
              style="margin-bottom: 0; max-width: 300px;"
            />
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { getOperationLogs, type OperationLog } from '@/api/system'

const loading = ref(false)
const logList = ref<OperationLog[]>([])
const searchText = ref('')
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const columns = [
  { title: '操作人', dataIndex: 'username', width: 120 },
  { title: '模块', dataIndex: 'module', width: 100 },
  { title: '动作', dataIndex: 'action', width: 100 },
  { title: '方法', key: 'method', width: 100 },
  { title: '路径', dataIndex: 'path', ellipsis: true },
  { title: '参数', key: 'params', width: 300 },
  { title: '状态码', key: 'response_code', width: 100 },
  { title: '耗时(ms)', dataIndex: 'response_time', width: 100 },
  { title: 'IP地址', dataIndex: 'ip', width: 150 },
  { title: '操作时间', dataIndex: 'created_at', width: 180 },
]

onMounted(() => {
  fetchLogs()
})

async function fetchLogs() {
  loading.value = true
  try {
    const res = await getOperationLogs({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value
    })
    logList.value = res.data.results
    pagination.total = res.data.count
  } catch (error) {
    message.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchLogs()
}

function handleSearch() {
  pagination.current = 1
  fetchLogs()
}

function getMethodColor(method: string) {
  const map: Record<string, string> = {
    GET: 'blue',
    POST: 'green',
    PUT: 'orange',
    DELETE: 'red',
    PATCH: 'orange'
  }
  return map[method] || 'default'
}
</script>

<style scoped>
.logs-page {
  padding: 0;
}
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}
.actions {
  display: flex;
  gap: 16px;
}
.table-card {
  border-radius: 8px;
}
</style>
