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
        </a-radio-group>
      </a-form-item>

      <!-- 1. 直接映射配置 -->
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

      <!-- 2. 对照表转换配置 -->
      <template v-else-if="formState.field_type === 'lookup'">
        <a-form-item label="源字段 (查找键)" required help="用于在对照表中查找的源字段">
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
                <a-select 
                  v-model:value="formState.reference_name_column" 
                  placeholder="选择字段"
                  show-search
                >
                  <a-select-option v-for="field in currentReferenceSheetFields" :key="field.name" :value="field.name">
                    {{ field.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="返回字段" required>
                <a-select 
                  v-model:value="formState.reference_code_column" 
                  placeholder="选择字段"
                  show-search
                >
                  <a-select-option v-for="field in currentReferenceSheetFields" :key="field.name" :value="field.name">
                    {{ field.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
        </a-card>
      </template>

      <!-- 3. 计算字段配置 -->
      <template v-else-if="formState.field_type === 'computed'">
        <a-form-item label="计算表达式" required help="支持简单的数学运算，使用 {字段名} 引用源字段，例如: {原值} / 12">
          <a-textarea 
            v-model:value="formState.compute_expression" 
            placeholder="例如: {使用月限} / 12" 
            :rows="3" 
          />
          <div class="field-tags">
            <span class="tag-label">可用字段(点击插入):</span>
            <a-tag 
              v-for="field in sourceFields.slice(0, 10)" 
              :key="field.name" 
              color="blue"
              @click="insertFieldToExpression(field.name)"
              style="cursor: pointer; margin-bottom: 4px;"
            >
              {{ field.name }}
            </a-tag>
          </div>
        </a-form-item>
      </template>

      <!-- 4. 默认值配置 -->
      <template v-else-if="formState.field_type === 'default'">
        <a-form-item label="默认值" required>
          <a-input v-model:value="formState.default_value" placeholder="请输入固定的默认值" />
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
import { reactive, computed, watch } from 'vue'
import type { MappingField, SheetInfo } from '@/api/processing'

const props = defineProps<{
  initialData?: Partial<MappingField>,
  sourceFields: { name: string, index: number }[],
  referenceSheets: SheetInfo[]
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
  ...props.initialData
})

const sourceFieldOptions = computed(() => {
  return props.sourceFields.map(f => ({ label: f.name, value: f.name }))
})

const currentReferenceSheetFields = computed(() => {
  if (!formState.reference_sheet) return []
  const sheet = props.referenceSheets.find(s => s.sheet_name === formState.reference_sheet)
  return sheet ? sheet.fields : []
})

function handleReferenceSheetChange() {
  formState.reference_name_column = undefined
  formState.reference_code_column = undefined
}

function insertFieldToExpression(fieldName: string) {
  formState.compute_expression = (formState.compute_expression || '') + `{${fieldName}}`
}

function handleConfirm() {
  emit('confirm', { ...formState })
}

// 监听初始数据变化
watch(() => props.initialData, (val) => {
  if (val) {
    Object.assign(formState, val)
    // 确保默认类型
    if (!formState.field_type) formState.field_type = 'direct'
  }
}, { deep: true })
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
}

.tag-label {
  margin-right: 8px;
  color: #666;
  font-size: 12px;
}

.actions {
  text-align: right;
}
</style>
