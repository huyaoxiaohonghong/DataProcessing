<template>
  <div class="lineage-designer">
    <a-alert
      type="info"
      show-icon
      message="Sheet 血缘决定了任务执行顺序：上游 Sheet 先执行，结果可被下游通过跨Sheet引用/表达式使用。"
      style="margin-bottom: 16px"
    />

    <!-- Sheet 血缘 -->
    <a-card size="small" title="Sheet 血缘关系" class="section-card">
      <template #extra>
        <a-button type="primary" size="small" @click="addSheetLineage" :disabled="targetSheets.length < 2">
          <template #icon><PlusOutlined /></template>
          新增关系
        </a-button>
      </template>

      <a-empty v-if="!sheetLineages.length" description="暂未配置 Sheet 血缘" />

      <a-table
        v-else
        :columns="sheetCols"
        :data-source="sheetLineages"
        :pagination="false"
        size="small"
        row-key="_rk"
      >
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === 'upstream'">
            <a-select
              v-model:value="record.upstream"
              size="small"
              style="width: 100%"
              :options="sheetOptions"
              placeholder="上游 Sheet"
            />
          </template>
          <template v-else-if="column.key === 'downstream'">
            <a-select
              v-model:value="record.downstream"
              size="small"
              style="width: 100%"
              :options="sheetOptions"
              placeholder="下游 Sheet"
            />
          </template>
          <template v-else-if="column.key === 'relation_type'">
            <a-select v-model:value="record.relation_type" size="small" style="width: 100%">
              <a-select-option value="derived">派生</a-select-option>
              <a-select-option value="aggregated">聚合</a-select-option>
              <a-select-option value="joined">关联</a-select-option>
              <a-select-option value="reference">引用</a-select-option>
            </a-select>
          </template>
          <template v-else-if="column.key === 'description'">
            <a-input v-model:value="record.description" size="small" placeholder="关系说明（可选）" />
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" danger size="small" @click="removeSheetLineage(index)">删除</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 字段血缘 -->
    <a-card size="small" title="字段血缘关系" class="section-card" style="margin-top: 16px">
      <template #extra>
        <a-space>
          <a-button size="small" @click="autoDeriveFieldLineages" :disabled="targetSheets.length < 2">
            <template #icon><ThunderboltOutlined /></template>
            自动推导
          </a-button>
          <a-button type="primary" size="small" @click="addFieldLineage" :disabled="targetSheets.length < 2">
            <template #icon><PlusOutlined /></template>
            新增
          </a-button>
        </a-space>
      </template>

      <a-empty v-if="!fieldLineages.length" description="暂未配置字段血缘" />

      <a-table
        v-else
        :columns="fieldCols"
        :data-source="fieldLineages"
        :pagination="{ pageSize: 10 }"
        size="small"
        row-key="_rk"
      >
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === 'upstream_sheet'">
            <a-select
              v-model:value="record.upstream_sheet"
              size="small"
              style="width: 100%"
              :options="sheetOptions"
              @change="() => { record.upstream_field = '' }"
            />
          </template>
          <template v-else-if="column.key === 'upstream_field'">
            <a-select
              v-model:value="record.upstream_field"
              size="small"
              style="width: 100%"
              :options="fieldOptionsOfSheet(record.upstream_sheet)"
              placeholder="字段"
              show-search
            />
          </template>
          <template v-else-if="column.key === 'downstream_sheet'">
            <a-select
              v-model:value="record.downstream_sheet"
              size="small"
              style="width: 100%"
              :options="sheetOptions"
              @change="() => { record.downstream_field = '' }"
            />
          </template>
          <template v-else-if="column.key === 'downstream_field'">
            <a-select
              v-model:value="record.downstream_field"
              size="small"
              style="width: 100%"
              :options="fieldOptionsOfSheet(record.downstream_sheet)"
              placeholder="字段"
              show-search
            />
          </template>
          <template v-else-if="column.key === 'transform'">
            <a-select v-model:value="record.transform" size="small" style="width: 100%">
              <a-select-option value="direct">直接</a-select-option>
              <a-select-option value="computed">计算</a-select-option>
              <a-select-option value="aggregated">聚合</a-select-option>
              <a-select-option value="lookup">对照</a-select-option>
            </a-select>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" danger size="small" @click="removeFieldLineage(index)">删除</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 拓扑顺序预览 -->
    <a-card size="small" title="执行顺序预览" class="section-card" style="margin-top: 16px">
      <a-alert
        v-if="topoOrder.cycle"
        type="error"
        show-icon
        message="检测到循环依赖"
        description="请检查 Sheet 血缘，存在环的部分将退化按 Sheet 顺序执行。"
        style="margin-bottom: 12px"
      />
      <a-steps :current="topoOrder.order.length - 1" size="small" :items="topoOrder.order.map((o, i) => ({ title: o, description: `第 ${i + 1} 步` }))" />
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { PlusOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import { topoSortSheets } from '@/composables/useSheetTopoSort'
import type { MappingTargetSheet, SheetLineageEdge, FieldLineageEdge } from '@/api/processing'

const props = defineProps<{
  targetSheets: MappingTargetSheet[]
  sheetLineages: Array<SheetLineageEdge & { _rk?: number }>
  fieldLineages: Array<FieldLineageEdge & { _rk?: number }>
}>()

const emit = defineEmits<{
  (e: 'update:sheetLineages', v: Array<SheetLineageEdge & { _rk?: number }>): void
  (e: 'update:fieldLineages', v: Array<FieldLineageEdge & { _rk?: number }>): void
}>()

let keySeed = 1
function nextKey() { return keySeed++ }

// 保证每条记录有 _rk，方便 Ant Design Vue 做 row-key
watch(
  () => props.sheetLineages,
  list => {
    list.forEach(l => { if (l._rk == null) l._rk = nextKey() })
  },
  { immediate: true, deep: true }
)
watch(
  () => props.fieldLineages,
  list => {
    list.forEach(l => { if (l._rk == null) l._rk = nextKey() })
  },
  { immediate: true, deep: true }
)

const sheetOptions = computed(() =>
  props.targetSheets.map(s => ({
    label: s.display_name ? `${s.sheet_name}（${s.display_name}）` : s.sheet_name,
    value: s.sheet_name
  }))
)

function fieldOptionsOfSheet(sheetName: string) {
  const sheet = props.targetSheets.find(s => s.sheet_name === sheetName)
  if (!sheet) return []
  return sheet.fields.map(f => ({ label: f.target_field, value: f.target_field }))
}

const sheetCols = [
  { title: '上游 Sheet', key: 'upstream', width: 180 },
  { title: '下游 Sheet', key: 'downstream', width: 180 },
  { title: '关系类型', key: 'relation_type', width: 120 },
  { title: '描述', key: 'description' },
  { title: '操作', key: 'action', width: 80, fixed: 'right' }
]

const fieldCols = [
  { title: '上游 Sheet', key: 'upstream_sheet', width: 160 },
  { title: '上游字段', key: 'upstream_field', width: 160 },
  { title: '下游 Sheet', key: 'downstream_sheet', width: 160 },
  { title: '下游字段', key: 'downstream_field', width: 160 },
  { title: '传播方式', key: 'transform', width: 120 },
  { title: '操作', key: 'action', width: 80, fixed: 'right' }
]

function addSheetLineage() {
  if (props.targetSheets.length < 2) return
  const first = props.targetSheets[0]
  const second = props.targetSheets[1]
  if (!first || !second) return
  const list = [...props.sheetLineages, {
    _rk: nextKey(),
    upstream: first.sheet_name,
    downstream: second.sheet_name,
    relation_type: 'derived' as const,
    description: ''
  }]
  emit('update:sheetLineages', list)
}

function removeSheetLineage(index: number) {
  const list = props.sheetLineages.slice()
  list.splice(index, 1)
  emit('update:sheetLineages', list)
}

function addFieldLineage() {
  if (props.targetSheets.length < 2) return
  const first = props.targetSheets[0]
  const second = props.targetSheets[1]
  if (!first || !second) return
  const list = [...props.fieldLineages, {
    _rk: nextKey(),
    upstream_sheet: first.sheet_name,
    upstream_field: '',
    downstream_sheet: second.sheet_name,
    downstream_field: '',
    transform: 'direct' as const,
    note: ''
  }]
  emit('update:fieldLineages', list)
}

function removeFieldLineage(index: number) {
  const list = props.fieldLineages.slice()
  list.splice(index, 1)
  emit('update:fieldLineages', list)
}

/**
 * 自动推导：对于下游 sheet 的 cross_sheet_ref 字段，按 source_target_sheet_name +
 * source_target_field 生成字段血缘。
 */
function autoDeriveFieldLineages() {
  const existing = new Set(
    props.fieldLineages.map(
      fl => `${fl.upstream_sheet}::${fl.upstream_field}->${fl.downstream_sheet}::${fl.downstream_field}`
    )
  )
  const additions: Array<FieldLineageEdge & { _rk?: number }> = []

  props.targetSheets.forEach(downSheet => {
    downSheet.fields.forEach(fd => {
      if (fd.field_type === 'cross_sheet_ref' && fd.source_target_sheet_name && fd.source_target_field) {
        const key = `${fd.source_target_sheet_name}::${fd.source_target_field}->${downSheet.sheet_name}::${fd.target_field}`
        if (!existing.has(key)) {
          additions.push({
            _rk: nextKey(),
            upstream_sheet: fd.source_target_sheet_name,
            upstream_field: fd.source_target_field,
            downstream_sheet: downSheet.sheet_name,
            downstream_field: fd.target_field,
            transform: fd.aggregation ? 'aggregated' : 'direct',
            note: fd.aggregation ? `聚合方式: ${fd.aggregation}` : ''
          })
          existing.add(key)
        }
      }
    })
  })

  if (additions.length) {
    emit('update:fieldLineages', [...props.fieldLineages, ...additions])
  }
}

// 拓扑排序预览（使用共享 composable，与后端 topo_sort_sheets 规则对齐：
// 最小堆按 (sort_order, sheet_name) 稳定出队，自环/未知节点的边被忽略，
// 有环时返回 (sort_order, sheet_name) 升序兜底序列 + cycle = true）
const topoOrder = computed(() =>
  topoSortSheets(props.targetSheets, props.sheetLineages),
)
</script>

<style scoped>
.lineage-designer {
  padding: 4px 0;
}

.section-card :deep(.ant-card-body) {
  padding: 12px 16px;
}
</style>
