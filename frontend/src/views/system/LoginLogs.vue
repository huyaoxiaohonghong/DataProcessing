<template>
  <div class="logs-page">
    <div class="header-actions">
      <h2 class="page-title">登录日志</h2>
      <div class="actions">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索用户名或IP..."
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
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status ? 'success' : 'error'">
              {{ record.status ? '成功' : '失败' }}
            </a-tag>
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
import { getLoginLogs, type LoginLog } from '@/api/system'

const loading = ref(false)
const logList = ref<LoginLog[]>([])
const searchText = ref('')
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const columns = [
  { title: '用户名', dataIndex: 'username', width: 150 },
  { title: 'IP地址', dataIndex: 'ip', width: 150 },
  { title: '状态', key: 'status', width: 100 },
  { title: '提示信息', dataIndex: 'message' },
  { title: ' User Agent', dataIndex: 'user_agent', ellipsis: true },
  { title: '登录时间', dataIndex: 'created_at', width: 180 },
]

onMounted(() => {
  fetchLogs()
})

async function fetchLogs() {
  loading.value = true
  try {
    const res = await getLoginLogs({
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

.actions {
  display: flex;
  gap: 16px;
}
</style>
