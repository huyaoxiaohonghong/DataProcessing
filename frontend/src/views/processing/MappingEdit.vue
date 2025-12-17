<template>
  <div class="mapping-edit">
    <!-- 页面头部 -->
    <div class="page-header">
      <a-page-header
        :title="isEdit ? '编辑映射配置' : '新建映射配置'"
        @back="$router.back()"
      >
        <template #extra>
          <a-space>
            <a-button @click="$router.back()">取消</a-button>
            <a-button type="primary" :loading="saving" @click="handleSave">
              保存配置
            </a-button>
          </a-space>
        </template>
      </a-page-header>
    </div>

    <!-- 步骤条 -->
    <a-card class="steps-card">
      <a-steps :current="currentStep" :items="stepItems" />
    </a-card>

    <!-- 步骤1: 文件选择 -->
    <a-card v-show="currentStep === 0" class="form-card" title="基本信息与文件选择">
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="配置名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入配置名称" />
        </a-form-item>

        <a-form-item label="配置描述" name="description">
          <a-textarea
            v-model:value="formData.description"
            placeholder="请输入配置描述（可选）"
            :rows="3"
          />
        </a-form-item>

        <a-divider>源文件配置</a-divider>

        <a-form-item label="源数据文件" name="source_file">
          <a-select
            v-model:value="formData.source_file"
            placeholder="请选择源数据文件"
            show-search
            :filter-option="filterOption"
            @change="handleSourceFileChange"
          >
            <a-select-option v-for="file in fileList" :key="file.id" :value="file.id">
              {{ file.name }} ({{ file.original_name }})
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="源文件工作表" name="source_sheet">
          <a-select
            v-model:value="formData.source_sheet"
            placeholder="请选择工作表"
            :disabled="!sourceSheets.length"
            @change="handleSourceSheetChange"
          >
            <a-select-option v-for="sheet in sourceSheets" :key="sheet.sheet_name" :value="sheet.sheet_name">
              {{ sheet.sheet_name }} ({{ sheet.fields.length }} 个字段)
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-divider>对照文件配置（可选）</a-divider>

        <a-form-item label="对照文件" name="reference_file">
          <a-select
            v-model:value="formData.reference_file"
            placeholder="请选择对照文件（可选）"
            show-search
            allow-clear
            :filter-option="filterOption"
            @change="handleReferenceFileChange"
          >
            <a-select-option v-for="file in fileList" :key="file.id" :value="file.id">
              {{ file.name }} ({{ file.original_name }})
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="对照文件工作表" name="reference_sheet">
          <a-select
            v-model:value="formData.reference_sheet"
            placeholder="请选择工作表"
            :disabled="!referenceSheets.length"
            @change="handleReferenceSheetChange"
          >
            <a-select-option v-for="sheet in referenceSheets" :key="sheet.sheet_name" :value="sheet.sheet_name">
              {{ sheet.sheet_name }} ({{ sheet.fields.length }} 个字段)
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-divider>目标模板配置</a-divider>

        <a-form-item label="目标模板" name="target_template">
          <a-select
            v-model:value="formData.target_template"
            placeholder="请选择目标模板文件"
            show-search
            :filter-option="filterOption"
            @change="handleTargetFileChange"
          >
            <a-select-option v-for="file in fileList" :key="file.id" :value="file.id">
              {{ file.name }} ({{ file.original_name }})
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="目标模板工作表" name="target_sheet">
          <a-select
            v-model:value="formData.target_sheet"
            placeholder="请选择工作表"
            :disabled="!targetSheets.length"
            @change="handleTargetSheetChange"
          >
            <a-select-option v-for="sheet in targetSheets" :key="sheet.sheet_name" :value="sheet.sheet_name">
              {{ sheet.sheet_name }} ({{ sheet.fields.length }} 个字段)
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 4, span: 16 }">
          <a-button type="primary" @click="goToMapping" :disabled="!canProceedToMapping">
            下一步：配置字段映射
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 步骤2: 字段映射配置 -->
    <div v-show="currentStep === 1" class="mapping-config-container">
      <!-- 顶部操作栏 -->
      <a-card class="mapping-toolbar" :bordered="false">
        <div class="toolbar-content">
          <a-space>
            <a-button @click="currentStep = 0">
              <template #icon><LeftOutlined /></template>
              返回上一步
            </a-button>
            <a-divider type="vertical" />
            <a-button @click="autoMatch">
              <template #icon><ThunderboltOutlined /></template>
              智能匹配
            </a-button>
            <a-button @click="clearAllMappings" danger>
              <template #icon><DeleteOutlined /></template>
              清空配置
            </a-button>
          </a-space>
          <div class="mapping-stats">
            <a-space>
              <a-tag color="blue">目标字段: {{ targetFields.length }}</a-tag>
              <a-tag color="green">已配置: {{ mappedCount }}</a-tag>
              <a-tag color="orange">未配置: {{ unmappedCount }}</a-tag>
            </a-space>
          </div>
        </div>
      </a-card>

      <!-- 主体内容：字段映射列表 -->
      <a-card class="mapping-table-card" :bordered="false">
        <a-table
          :columns="mappingTableColumns"
          :data-source="targetFields"
          row-key="name"
          :pagination="false"
          :scroll="{ y: 600 }"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <!-- 目标字段列 -->
            <template v-if="column.key === 'target_field'">
              <div class="target-field-cell">
                <span class="field-index">{{ record.index + 1 }}</span>
                <span class="field-name">{{ record.name }}</span>
                <a-tag v-if="getMappingForTarget(record.name)" color="green" class="status-tag">
                  <CheckCircleOutlined /> 已配置
                </a-tag>
                <a-tag v-else color="default" class="status-tag">
                  待配置
                </a-tag>
              </div>
            </template>

            <!-- 映射规则列 -->
            <template v-else-if="column.key === 'rule'">
              <div class="rule-cell">
                <template v-if="getMappingForTarget(record.name)">
                  <a-tag :color="getFieldTypeColor(getMappingForTarget(record.name)?.field_type)">
                    {{ getFieldTypeLabel(getMappingForTarget(record.name)?.field_type) }}
                  </a-tag>
                  <span class="rule-desc">
                    {{ getMappingDescription(getMappingForTarget(record.name)) }}
                  </span>
                </template>
                <span v-else class="text-gray">暂无映射规则</span>
              </div>
            </template>

            <!-- 操作列 -->
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="openFieldConfig(record)">
                  <EditOutlined /> 配置
                </a-button>
                <a-button 
                  v-if="getMappingForTarget(record.name)" 
                  type="link" 
                  danger 
                  size="small" 
                  @click="removeMapping(record.name)"
                >
                  清除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- 字段配置抽屉 -->
    <a-drawer
      v-model:open="drawerVisible"
      title="配置字段映射规则"
      width="600"
      :mask-closable="false"
    >
      <div v-if="currentEditingTarget" class="drawer-header-info">
        <p>目标字段：<strong>{{ currentEditingTarget.name }}</strong></p>
      </div>
      
      <MappingRuleConfig
        v-if="drawerVisible && currentEditingTarget"
        :initial-data="getMappingForTarget(currentEditingTarget.name) || {}"
        :source-fields="sourceFields"
        :reference-sheets="referenceSheets"
        @confirm="saveFieldConfig"
        @cancel="drawerVisible = false"
      />
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  LeftOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
  EditOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import { getFiles, type FileInfo } from '@/api/file'
import {
  getMapping,
  createMapping,
  updateMapping,
  parseFileFields,
  type MappingField,
  type SheetInfo
} from '@/api/processing'
import MappingRuleConfig from '@/components/processing/MappingRuleConfig.vue'

// 路由
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const mappingId = computed(() => Number(route.params.id) || 0)

// 步骤控制
const currentStep = ref(0)
const stepItems = [
  { title: '文件选择', description: '选择源文件和目标模板' },
  { title: '字段映射', description: '可视化配置字段映射' }
]

// 加载状态
const saving = ref(false)
const formRef = ref()

// 文件列表
const fileList = ref<FileInfo[]>([])

// 工作表信息
const sourceSheets = ref<SheetInfo[]>([])
const referenceSheets = ref<SheetInfo[]>([])
const targetSheets = ref<SheetInfo[]>([])

// 字段列表
const sourceFields = ref<{ name: string; index: number }[]>([])
const referenceFields = ref<{ name: string; index: number }[]>([])
const targetFields = ref<{ name: string; index: number }[]>([])

// 表单数据
const formData = reactive({
  name: '',
  description: '',
  source_file: undefined as number | undefined,
  source_sheet: '',
  reference_file: undefined as number | undefined,
  reference_sheet: '',
  target_template: undefined as number | undefined,
  target_sheet: '',
  status: 'draft',
  fields: [] as MappingField[]
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入配置名称' }],
  source_file: [{ required: true, message: '请选择源数据文件' }],
  source_sheet: [{ required: true, message: '请选择源文件工作表' }],
  target_template: [{ required: true, message: '请选择目标模板文件' }],
  target_sheet: [{ required: true, message: '请选择目标模板工作表' }]
}

// 映射表格列定义
const mappingTableColumns = [
  { title: '目标字段', key: 'target_field', width: 250 },
  { title: '映射规则', key: 'rule' },
  { title: '操作', key: 'action', width: 150, fixed: 'right' }
]

// 抽屉状态
const drawerVisible = ref(false)
const currentEditingTarget = ref<{ name: string; index: number } | null>(null)

// 计算属性
const canProceedToMapping = computed(() => {
  return formData.source_file && formData.source_sheet &&
         formData.target_template && formData.target_sheet &&
         sourceFields.value.length > 0 && targetFields.value.length > 0
})

const mappedCount = computed(() => formData.fields.length)
const unmappedCount = computed(() => targetFields.value.length - mappedCount.value)

// 过滤选项
function filterOption(input: string, option: any) {
  return option.children[0].children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// 加载文件列表
async function loadFiles() {
  try {
    const res = await getFiles({ page_size: 1000 })
    fileList.value = res.data.results || []
  } catch (error) {
    console.error('加载文件列表失败:', error)
  }
}

// 解析文件字段
async function parseFields(fileId: number): Promise<SheetInfo[]> {
  try {
    const res = await parseFileFields(fileId)
    return res.data.data?.sheets || []
  } catch (error) {
    console.error('解析文件字段失败:', error)
    return []
  }
}

// 源文件变更
async function handleSourceFileChange(fileId: number) {
  formData.source_sheet = ''
  sourceFields.value = []
  sourceSheets.value = []
  
  if (fileId) {
    sourceSheets.value = await parseFields(fileId)
    const firstSheet = sourceSheets.value[0]
    if (sourceSheets.value.length === 1 && firstSheet) {
      formData.source_sheet = firstSheet.sheet_name
      handleSourceSheetChange(firstSheet.sheet_name)
    }
  }
}

// 源工作表变更
function handleSourceSheetChange(sheetName: string) {
  const sheet = sourceSheets.value.find(s => s.sheet_name === sheetName)
  sourceFields.value = sheet?.fields || []
  clearAllMappings()
}

// 对照文件变更
async function handleReferenceFileChange(fileId: number | undefined) {
  formData.reference_sheet = ''
  referenceFields.value = []
  referenceSheets.value = []
  
  if (fileId) {
    referenceSheets.value = await parseFields(fileId)
    const firstRefSheet = referenceSheets.value[0]
    if (referenceSheets.value.length === 1 && firstRefSheet) {
      formData.reference_sheet = firstRefSheet.sheet_name
      handleReferenceSheetChange(firstRefSheet.sheet_name)
    }
  }
}

// 对照工作表变更
function handleReferenceSheetChange(sheetName: string) {
  const sheet = referenceSheets.value.find(s => s.sheet_name === sheetName)
  referenceFields.value = sheet?.fields || []
}

// 目标文件变更
async function handleTargetFileChange(fileId: number) {
  formData.target_sheet = ''
  targetFields.value = []
  targetSheets.value = []
  
  if (fileId) {
    targetSheets.value = await parseFields(fileId)
    const firstTargetSheet = targetSheets.value[0]
    if (targetSheets.value.length === 1 && firstTargetSheet) {
      formData.target_sheet = firstTargetSheet.sheet_name
      handleTargetSheetChange(firstTargetSheet.sheet_name)
    }
  }
}

// 目标工作表变更
function handleTargetSheetChange(sheetName: string) {
  const sheet = targetSheets.value.find(s => s.sheet_name === sheetName)
  targetFields.value = sheet?.fields || []
  clearAllMappings()
}

// 进入映射步骤
function goToMapping() {
  if (!canProceedToMapping.value) {
    message.warning('请先完成文件选择')
    return
  }
  currentStep.value = 1
}

// 判断目标字段是否已映射
function isTargetMapped(index: number): boolean {
  return formData.fields.some(f => f.target_field_index === index)
}

// 获取映射类型标签
function getFieldTypeLabel(type: string | undefined): string {
  const map: Record<string, string> = {
    'direct': '直接映射',
    'lookup': '对照表转换',
    'computed': '计算字段',
    'default': '默认值',
    'source_to_target': '直接映射',
    'source_to_ref': '源→对照',
    'ref_to_target': '对照→目标',
    'source_ref_target': '对照表转换'
  }
  return map[type || ''] || type || ''
}

// 获取映射类型颜色
function getFieldTypeColor(type: string | undefined): string {
  const map: Record<string, string> = {
    'direct': 'blue',
    'lookup': 'purple',
    'computed': 'orange',
    'default': 'cyan',
    'source_to_target': 'blue',
    'source_ref_target': 'purple'
  }
  return map[type || ''] || 'default'
}

// 根据目标字段名获取映射配置
function getMappingForTarget(targetFieldName: string): MappingField | undefined {
  return formData.fields.find(f => f.target_field === targetFieldName)
}

// 获取映射描述
function getMappingDescription(mapping: MappingField | undefined): string {
  if (!mapping) return ''
  
  switch (mapping.field_type) {
    case 'direct':
    case 'source_to_target':
      return `来源: ${mapping.source_field}`
    case 'lookup':
    case 'source_ref_target':
      return `${mapping.source_field} → [${mapping.reference_sheet || '对照表'}] → 编码`
    case 'computed':
      return `公式: ${mapping.compute_expression}`
    case 'default':
      return `固定值: ${mapping.default_value}`
    default:
      return mapping.source_field || ''
  }
}

// 打开字段配置抽屉
function openFieldConfig(targetField: { name: string; index: number }) {
  currentEditingTarget.value = targetField
  drawerVisible.value = true
}

// 保存字段配置
function saveFieldConfig(config: Partial<MappingField>) {
  if (!currentEditingTarget.value) return

  // 查找是否已存在该目标字段的映射
  const existingIndex = formData.fields.findIndex(
    f => f.target_field === currentEditingTarget.value!.name
  )

  const newMapping: MappingField = {
    source_field: config.source_field || '',
    source_field_index: sourceFields.value.find(f => f.name === config.source_field)?.index ?? -1,
    reference_sheet: config.reference_sheet || '',
    reference_name_column: config.reference_name_column || '',
    reference_code_column: config.reference_code_column || '',
    reference_field: config.reference_name_column || '',
    reference_field_index: -1,
    target_field: currentEditingTarget.value.name,
    target_field_index: currentEditingTarget.value.index,
    field_type: config.field_type || 'direct',
    default_value: config.default_value || '',
    compute_expression: config.compute_expression || '',
    transform_rule: config.transform_rule || null,
    sort_order: existingIndex >= 0 ? (formData.fields[existingIndex]?.sort_order ?? formData.fields.length + 1) : formData.fields.length + 1
  }

  if (existingIndex >= 0) {
    formData.fields[existingIndex] = newMapping
  } else {
    formData.fields.push(newMapping)
  }

  drawerVisible.value = false
  currentEditingTarget.value = null
  message.success('映射配置已保存')
}

// 删除映射（根据目标字段名）
function removeMapping(targetFieldName: string) {
  const index = formData.fields.findIndex(f => f.target_field === targetFieldName)
  if (index >= 0) {
    formData.fields.splice(index, 1)
    // 重新编号
    formData.fields.forEach((f, i) => {
      f.sort_order = i + 1
    })
  }
}

// 清空所有映射
function clearAllMappings() {
  formData.fields = []
}

// 智能匹配
function autoMatch() {
  // 清空现有映射
  clearAllMappings()

  // 按名称相似度匹配
  sourceFields.value.forEach(sourceField => {
    // 查找名称相同或相似的目标字段
    const matchedTarget = targetFields.value.find(targetField => {
      // 完全匹配
      if (targetField.name === sourceField.name) return true
      // 忽略大小写匹配
      if (targetField.name.toLowerCase() === sourceField.name.toLowerCase()) return true
      // 包含匹配
      if (targetField.name.includes(sourceField.name) || sourceField.name.includes(targetField.name)) return true
      return false
    })

    if (matchedTarget && !isTargetMapped(matchedTarget.index)) {
      const newField: MappingField = {
        source_field: sourceField.name,
        source_field_index: sourceField.index,
        reference_sheet: '',
        reference_name_column: '',
        reference_code_column: '',
        reference_field: '',
        reference_field_index: -1,
        target_field: matchedTarget.name,
        target_field_index: matchedTarget.index,
        field_type: 'direct',
        default_value: '',
        compute_expression: '',
        transform_rule: null,
        sort_order: formData.fields.length + 1
      }
      formData.fields.push(newField)
    }
  })

  message.success(`智能匹配完成，共匹配 ${formData.fields.length} 个字段`)
}

// 保存配置
async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    currentStep.value = 0
    message.warning('请完成基本信息填写')
    return
  }

  if (formData.fields.length === 0) {
    message.warning('请至少添加一个字段映射')
    return
  }

  saving.value = true
  try {
    const data = {
      name: formData.name,
      description: formData.description,
      source_file: formData.source_file,
      source_sheet: formData.source_sheet,
      reference_file: formData.reference_file || undefined,
      reference_sheet: formData.reference_sheet || undefined,
      target_template: formData.target_template,
      target_sheet: formData.target_sheet,
      status: formData.status,
      fields: formData.fields
    }

    if (isEdit.value) {
      await updateMapping(mappingId.value, data)
      message.success('配置更新成功')
    } else {
      await createMapping(data)
      message.success('配置创建成功')
    }
    
    router.push('/processing/mappings')
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

// 加载现有配置（编辑模式）
async function loadMapping() {
  if (!isEdit.value) return

  try {
    const res = await getMapping(mappingId.value)
    const data = res.data.data

    formData.name = data.name
    formData.description = data.description || ''
    formData.source_file = data.source_file
    formData.source_sheet = data.source_sheet
    formData.reference_file = data.reference_file
    formData.reference_sheet = data.reference_sheet
    formData.target_template = data.target_template
    formData.target_sheet = data.target_sheet
    formData.status = data.status
    formData.fields = data.fields || []

    // 加载对应的工作表信息
    if (formData.source_file) {
      sourceSheets.value = await parseFields(formData.source_file)
      const sheet = sourceSheets.value.find(s => s.sheet_name === formData.source_sheet)
      sourceFields.value = sheet?.fields || []
    }
    if (formData.reference_file) {
      referenceSheets.value = await parseFields(formData.reference_file)
      const sheet = referenceSheets.value.find(s => s.sheet_name === formData.reference_sheet)
      referenceFields.value = sheet?.fields || []
    }
    if (formData.target_template) {
      targetSheets.value = await parseFields(formData.target_template)
      const sheet = targetSheets.value.find(s => s.sheet_name === formData.target_sheet)
      targetFields.value = sheet?.fields || []
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    message.error('加载配置失败')
  }
}

// 初始化
onMounted(async () => {
  await loadFiles()
  await loadMapping()
})
</script>

<style scoped>
.mapping-edit {
  padding: 0;
}

.page-header {
  background: #fff;
  margin: -24px -24px 16px -24px;
  padding: 0;
}

.steps-card {
  margin-bottom: 16px;
}

.form-card {
  margin-bottom: 16px;
}

.mapping-canvas-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mapping-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mapping-toolbar :deep(.ant-card-body) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
}

.mapping-stats {
  display: flex;
  gap: 8px;
}

.mapping-visual-area {
  position: relative;
  display: flex;
  gap: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  border-radius: 12px;
  padding: 24px;
  min-height: 500px;
  overflow: hidden;
}

.connection-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.connection-line {
  fill: none;
  stroke: #1890ff;
  stroke-width: 2;
  opacity: 0.7;
  pointer-events: stroke;
  cursor: pointer;
  transition: all 0.3s ease;
}

.connection-line:hover {
  stroke-width: 3;
  opacity: 1;
}

.connection-line.active {
  stroke: #52c41a;
  stroke-width: 3;
  opacity: 1;
}

.temp-connection-line {
  fill: none;
  stroke: #1890ff;
  stroke-width: 2;
  stroke-dasharray: 5, 5;
  opacity: 0.5;
}

.field-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  z-index: 2;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-weight: 600;
}

.source-column .column-header {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.reference-column .column-header {
  background: linear-gradient(135deg, #722ed1 0%, #531dab 100%);
}

.target-column .column-header {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.field-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  max-height: 400px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
  background: #fafafa;
}

.field-item:hover {
  background: #e6f7ff;
  border-color: #91d5ff;
}

.field-item.selected {
  background: #e6f7ff;
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.field-item.mapped {
  background: #f6ffed;
  border-color: #b7eb8f;
}

.field-item.mapped:hover {
  border-color: #52c41a;
}

.source-field.selected {
  border-color: #1890ff;
  background: #e6f7ff;
}

.reference-field.selected {
  border-color: #722ed1;
  background: #f9f0ff;
}

.target-field.selected {
  border-color: #52c41a;
  background: #f6ffed;
}

.field-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #e8e8e8;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
  flex-shrink: 0;
}

.field-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mapped-icon {
  color: #52c41a;
  font-size: 16px;
  flex-shrink: 0;
}

.mapping-rules-card {
  margin-top: 16px;
}

.mapping-rules-card :deep(.ant-table) {
  font-size: 13px;
}

/* 滚动条美化 */
.field-list::-webkit-scrollbar {
  width: 6px;
}

.field-list::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 3px;
}

.field-list::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.field-list::-webkit-scrollbar-thumb:hover {
  background: #999;
}

/* 动画 */
@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(24, 144, 255, 0);
  }
}

.field-item.selected {
  animation: pulse 1.5s infinite;
}
</style>
