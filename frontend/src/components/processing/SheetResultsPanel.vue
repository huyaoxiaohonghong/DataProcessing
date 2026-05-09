<template>
  <div class="sheet-results-panel">
    <a-spin :spinning="loading" size="small">
      <a-alert
        v-if="errorMessage"
        type="error"
        show-icon
        :message="errorMessage"
        style="margin-bottom: 8px"
      />

      <a-empty v-if="!loading && !sheetResults.length" description="暂无 Sheet 执行结果（单 Sheet 任务不产生分 Sheet 明细）" />

      <a-table
        v-else
        :columns="columns"
        :data-source="sheetResults"
        :pagination="false"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ record.status_display }}</a-tag>
          </template>
          <template v-else-if="column.key === 'progress'">
            <a-progress
              :percent="Number(record.progress) || 0"
              :status="progressStatus(record.status)"
              size="small"
              style="max-width: 160px"
            />
          </template>
          <template v-else-if="column.key === 'rows'">
            <span>{{ record.success_rows }} / {{ record.total_rows }}</span>
            <a-tag v-if="record.error_rows > 0" color="red" style="margin-left: 4px">
              错误 {{ record.error_rows }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'duration'">
            {{ record.duration_ms || 0 }} ms
          </template>
          <template v-else-if="column.key === 'error_message'">
            <a-tooltip v-if="record.status === 'failed' && record.error_message" placement="topLeft">
              <template #title>{{ record.error_message }}</template>
              <InfoCircleOutlined style="color: #ff4d4f" />
            </a-tooltip>
            <span v-else style="color: #bfbfbf">—</span>
          </template>
        </template>
      </a-table>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import { InfoCircleOutlined } from '@ant-design/icons-vue'
import { getTaskSheetResults, type TaskSheetResult, type ProcessingTask } from '@/api/processing'

// Req 16.1 / 16.3: refreshKey recv'd from parent — increment to re-fetch.
interface Props {
  taskId: number
  taskStatus: ProcessingTask['status']
  refreshKey: number
}
const props = defineProps<Props>()

const loading = ref(false)
const errorMessage = ref('')
const sheetResults = ref<TaskSheetResult[]>([])

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await getTaskSheetResults(props.taskId)
    const body = res.data
    sheetResults.value = (body?.data || []) as TaskSheetResult[]
  } catch (e: any) {
    errorMessage.value = e?.message || '加载 Sheet 结果失败'
  } finally {
    loading.value = false
  }
}

// Refetch whenever the parent bumps refreshKey (first expand + polling tick).
watchEffect(() => {
  // Reference both props so Vue tracks changes
  void props.refreshKey
  void props.taskId
  load()
})

// -----------------------------------------------------------------------
// Styling helpers
// -----------------------------------------------------------------------

const columns = [
  { title: 'Sheet 名称', dataIndex: 'sheet_name', key: 'sheet_name', width: 160 },
  { title: '状态', key: 'status', width: 100 },
  { title: '进度', key: 'progress', width: 200 },
  { title: '行数 (成功/总数)', key: 'rows', width: 160 },
  { title: '耗时', key: 'duration', width: 100 },
  { title: '错误', key: 'error_message', width: 60 },
]

function statusColor(status: TaskSheetResult['status']) {
  switch (status) {
    case 'completed':
      return 'success'
    case 'running':
      return 'processing'
    case 'failed':
      return 'error'
    case 'skipped':
      return 'default'
    case 'pending':
    default:
      return 'default'
  }
}

function progressStatus(status: TaskSheetResult['status']): 'active' | 'exception' | 'success' | 'normal' {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  if (status === 'running') return 'active'
  return 'normal'
}
</script>

<style scoped>
.sheet-results-panel {
  padding: 8px 16px;
  background: var(--color-surface, rgba(255, 255, 255, 0.04));
  border-radius: 4px;
  color: var(--color-text);
}
</style>
