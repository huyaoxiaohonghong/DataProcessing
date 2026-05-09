<template>
  <div class="mapping-rule-config">
    <a-form layout="vertical" :model="formState">
      <!-- 映射类型选择 -->
      <a-form-item label="映射类型" required>
        <a-radio-group v-model:value="formState.field_type" button-style="solid">
          <a-radio-button value="direct">直接映射</a-radio-button>
          <a-radio-button value="lookup">对照表转换</a-radio-button>
          <a-radio-button value="computed">计算字段</a-radio-button>
          <a-radio-button value="default">默认值</a-radio-button>
          <a-radio-button value="cross_sheet_ref" v-if="upstreamSheets && upstreamSheets.length">跨Sheet引用</a-radio-button>
        </a-radio-group>
      </a-form-item>

      <!-- 1. 直接映射 -->
      <template v-if="formState.field_type === 'direct'">
        <a-form-item label="源字段" required help="选择源文件中对应的字段">
          <a-select
            v-model:value="formState.source_field"
            placeholder="请选择源字段"
            show-search
            :options="sourceFieldOptions"
          />
        </a-form-item>
      </template>

      <!-- 2. 对照表转换 -->
      <template v-else-if="formState.field_type === 'lookup'">
        <a-form-item label="源字段 (查找键)" required>
          <a-select
            v-model:value="formState.source_field"
            placeholder="请选择源字段"
            show-search
            :options="sourceFieldOptions"
          />
        </a-form-item>

        <a-card size="small" title="对照表配置" class="lookup-card">
          <a-form-item label="对照表 Sheet" required>
            <a-select
              v-model:value="formState.reference_sheet"
              placeholder="选择对照表Sheet"
              @change="handleReferenceSheetChange"
            >
              <a-select-option v-for="sheet in referenceSheets" :key="sheet.sheet_name" :value="sheet.sheet_name">
                {{ sheet.sheet_name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="查找字段" required>
                <a-select v-model:value="formState.reference_name_column" placeholder="选择字段" show-search>
                  <a-select-option v-for="field in currentReferenceSheetFields" :key="field.name" :value="field.name">
                    {{ field.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="返回字段" required>
                <a-select v-model:value="formState.reference_code_column" placeholder="选择字段" show-search>
                  <a-select-option v-for="field in currentReferenceSheetFields" :key="field.name" :value="field.name">
                    {{ field.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
        </a-card>
      </template>

      <!-- 3. 计算字段 -->
      <template v-else-if="formState.field_type === 'computed'">
        <a-form-item label="计算表达式" required help="使用 {字段名} 引用当前源字段；跨 sheet 引用使用 {目标Sheet名.字段}，支持 + - * /">
          <a-textarea
            v-model:value="formState.compute_expression"
            placeholder="例如: {使用月限} / 12 或 {部门汇总.总数} * 0.5"
            :rows="3"
          />
          <div class="field-tags">
            <span class="tag-label">源字段(点击插入):</span>
            <a-tag
              v-for="field in sourceFields.slice(0, 12)"
              :key="field.name"
              color="blue"
              @click="insertToken(`{${field.name}}`)"
              style="cursor: pointer; margin-bottom: 4px;"
            >
              {{ field.name }}
            </a-tag>
          </div>
          <div v-if="upstreamSheets && upstreamSheets.length" class="field-tags">
            <span class="tag-label">跨Sheet字段:</span>
            <a-select
              v-model:value="crossSheetPick"
              placeholder="选择上游Sheet字段后点击插入"
              style="width: 280px"
              size="small"
              show-search
            >
              <a-select-option
                v-for="opt in crossSheetOptions"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </a-select-option>
            </a-select>
            <a-button size="small" type="link" :disabled="!crossSheetPick" @click="insertToken(`{${crossSheetPick}}`)">
              插入
            </a-button>
          </div>
        </a-form-item>
      </template>

      <!-- 4. 默认值 -->
      <template v-else-if="formState.field_type === 'default'">
        <a-form-item label="默认值" required>
          <a-input v-model:value="formState.default_value" placeholder="请输入固定的默认值" />
        </a-form-item>
      </template>

      <!-- 5. 跨 Sheet 引用 -->
      <template v-else-if="formState.field_type === 'cross_sheet_ref'">
        <a-form-item label="引用上游 Sheet" required help="只能引用血缘上游的目标 Sheet，或其他已定义的目标 Sheet">
          <a-select
            v-model:value="formState.source_target_sheet_name"
            placeholder="请选择上游 Sheet"
            @change="handleUpstreamSheetChange"
          >
            <a-select-option
              v-for="s in upstreamSheets"
              :key="s.sheet_name"
              :value="s.sheet_name"
            >
              {{ s.display_name || s.sheet_name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="引用字段" required>
          <a-select
            v-model:value="formState.source_target_field"
            placeholder="请选择要引用的字段"
            show-search
          >
            <a-select-option
              v-for="f in currentUpstreamFields"
              :key="f.target_field"
              :value="f.target_field"
            >
              {{ f.target_field }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="聚合方式" help="多行上游数据时如何汇总；留空表示取第一行">
          <a-select v-model:value="formState.aggregation" allow-clear placeholder="不聚合（取首行）">
            <a-select-option value="sum">求和 SUM</a-select-option>
            <a-select-option value="count">计数 COUNT</a-select-option>
            <a-select-option value="avg">平均值 AVG</a-select-option>
            <a-select-option value="min">最小值 MIN</a-select-option>
            <a-select-option value="max">最大值 MAX</a-select-option>
            <a-select-option value="first">首行 FIRST</a-select-option>
          </a-select>
        </a-form-item>
      </template>

      <a-divider />
      <div class="actions">
        <a-button type="primary" @click="handleConfirm">确定</a-button>
        <a-button style="margin-left: 8px" @click="$emit('cancel')">取消</a-button>
      </div>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { reactive, computed, watch, ref } from 'vue'
import type { MappingField, MappingTargetSheet, SheetInfo } from '@/api/processing'

const props = defineProps<{
  initialData?: Partial<MappingField>
  sourceFields: { name: string; index: number }[]
  referenceSheets: SheetInfo[]
  /** 其它可作为上游引用的目标 Sheet（通常是拓扑上游） */
  upstreamSheets?: MappingTargetSheet[]
}>()

const emit = defineEmits(['confirm', 'cancel'])

const formState = reactive<Partial<MappingField>>({
  field_type: 'direct',
  source_field: undefined,
  reference_sheet: undefined,
  reference_name_column: undefined,
  reference_code_column: undefined,
  default_value: '',
  compute_expression: '',
  source_target_sheet_name: '',
  source_target_field: '',
  aggregation: '',
  ...props.initialData
})

const sourceFieldOptions = computed(() =>
  props.sourceFields.map(f => ({ label: f.name, value: f.name }))
)

const currentReferenceSheetFields = computed(() => {
  if (!formState.reference_sheet) return []
  const sheet = props.referenceSheets.find(s => s.sheet_name === formState.reference_sheet)
  return sheet ? sheet.fields : []
})

const currentUpstreamFields = computed(() => {
  if (!formState.source_target_sheet_name || !props.upstreamSheets) return []
  const s = props.upstreamSheets.find(x => x.sheet_name === formState.source_target_sheet_name)
  return s ? s.fields : []
})

const crossSheetOptions = computed(() => {
  const opts: { label: string; value: string }[] = []
  ;(props.upstreamSheets || []).forEach(s => {
    s.fields.forEach(f => {
      opts.push({
        label: `${s.display_name || s.sheet_name}.${f.target_field}`,
        value: `${s.sheet_name}.${f.target_field}`
      })
    })
  })
  return opts
})

const crossSheetPick = ref<string>('')

function handleReferenceSheetChange() {
  formState.reference_name_column = undefined
  formState.reference_code_column = undefined
}

function handleUpstreamSheetChange() {
  formState.source_target_field = ''
}

function insertToken(token: string) {
  formState.compute_expression = (formState.compute_expression || '') + token
}

function handleConfirm() {
  emit('confirm', { ...formState })
}

watch(
  () => props.initialData,
  val => {
    if (val) {
      Object.assign(formState, val)
      if (!formState.field_type) formState.field_type = 'direct'
    }
  },
  { deep: true }
)
</script>

<style scoped>
.mapping-rule-config {
  padding: 16px;
  background: #fff;
  border-radius: 4px;
}

.lookup-card {
  margin-top: 16px;
  background: #fafafa;
}

.field-tags {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-label {
  color: #666;
  font-size: 12px;
}

.actions {
  text-align: right;
}
</style>
