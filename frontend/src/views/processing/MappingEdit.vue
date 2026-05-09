<template>
  <div class="mapping-edit">
    <!-- 页面头部 -->
    <div class="header-actions">
      <h2 class="page-title">{{ isEdit ? '编辑映射配置' : '新建映射配置' }}</h2>
      <a-space>
        <a-button @click="$router.back()">取消</a-button>
        <a-button type="primary" :loading="saving" @click="handleSave">
          保存配置
        </a-button>
      </a-space>
    </div>

    <!-- 步骤条 -->
    <a-card class="steps-card">
      <a-steps :current="currentStep" :items="stepItems" />
    </a-card>

    <!-- ============ Step 0: 基本信息与文件选择 ============ -->
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
          <a-textarea v-model:value="formData.description" placeholder="请输入配置描述（可选）" :rows="3" />
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

        <a-form-item label="默认源工作表" name="source_sheet" help="多 Sheet 模式下，每个目标 Sheet 可覆盖此默认值">
          <a-select
            v-model:value="formData.source_sheet"
            placeholder="请选择工作表"
            :disabled="!sourceSheets.length"
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

        <a-form-item label="目标 Sheet（可多选）" help="勾选多个模板工作表进入多 Sheet 模式；仅勾选一个则保留单 Sheet 兼容模式">
          <a-checkbox-group
            v-model:value="selectedTemplateSheetNames"
            :disabled="!templateSheets.length"
            :options="templateSheets.map(s => ({ label: `${s.sheet_name} (${s.fields.length}字段)`, value: s.sheet_name }))"
          />
          <div v-if="!templateSheets.length" class="help-tip">请先选择目标模板文件</div>
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 4, span: 16 }">
          <a-button type="primary" @click="goToMapping" :disabled="!canProceedToMapping">
            下一步：配置字段映射
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- ============ Step 1: 字段映射配置（多 Sheet / Legacy 分支） ============ -->
    <div v-show="currentStep === 1" class="mapping-config-container">
      <!-- 顶部操作栏 -->
      <a-card class="mapping-toolbar" :bordered="false">
        <div class="toolbar-content">
          <a-space>
            <a-button @click="currentStep = 0">
              <template #icon><LeftOutlined /></template>
              上一步
            </a-button>
            <a-divider type="vertical" />
            <a-button @click="autoMatch">
              <template #icon><ThunderboltOutlined /></template>
              智能匹配
            </a-button>
            <a-button danger @click="clearCurrentSheetFields">
              <template #icon><DeleteOutlined /></template>
              清空当前 Sheet
            </a-button>
            <a-divider type="vertical" />
            <a-button v-if="uiMode === 'legacy_single' && legacyFields.length" @click="migrateLegacyToMultiSheet">
              <template #icon><PlusOutlined /></template>
              升级为多 Sheet 模式
            </a-button>
          </a-space>
          <div class="mapping-stats">
            <a-space>
              <a-tag color="blue">目标字段: {{ currentSheetTargetFields.length }}</a-tag>
              <a-tag color="green">已配置: {{ mappedCount }}</a-tag>
              <a-tag color="orange">未配置: {{ Math.max(unmappedCount, 0) }}</a-tag>
              <a-button type="primary" @click="currentStep = 2" :disabled="!canProceedToLineage">
                下一步：血缘
                <template #icon><RightOutlined /></template>
              </a-button>
            </a-space>
          </div>
        </div>
      </a-card>

      <!-- 多 Sheet 模式：Tabs -->
      <a-card v-if="uiMode === 'multi_sheet'" class="mapping-table-card" :bordered="false">
        <a-tabs
          v-model:activeKey="activeSheetName"
          type="editable-card"
          @edit="onTabEdit"
        >
          <a-tab-pane
            v-for="ts in formData.target_sheets"
            :key="ts.sheet_name"
            :closable="formData.target_sheets.length > 1"
          >
            <template #tab>
              <span>{{ ts.display_name || ts.sheet_name }}</span>
              <a-tag style="margin-left: 6px" :color="tabStatusColor(ts.status)">{{ ts.fields.length }}</a-tag>
            </template>

            <!-- Sheet 属性 -->
            <a-descriptions size="small" :column="2" bordered class="sheet-props">
              <a-descriptions-item label="Sheet 名">
                <span class="mono">{{ ts.sheet_name }}</span>
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-select v-model:value="ts.status" size="small" style="width: 130px">
                  <a-select-option value="draft">草稿</a-select-option>
                  <a-select-option value="ready">已就绪</a-select-option>
                  <a-select-option value="disabled">已禁用</a-select-option>
                </a-select>
              </a-descriptions-item>
              <a-descriptions-item label="展示名">
                <a-input v-model:value="ts.display_name" placeholder="展示名（可选）" size="small" />
              </a-descriptions-item>
              <a-descriptions-item label="源 Sheet">
                <a-select v-model:value="ts.source_sheet" size="small" style="width: 100%" allow-clear placeholder="继承默认源 Sheet">
                  <a-select-option v-for="s in sourceSheets" :key="s.sheet_name" :value="s.sheet_name">
                    {{ s.sheet_name }}
                  </a-select-option>
                </a-select>
              </a-descriptions-item>
              <a-descriptions-item label="说明" :span="2">
                <a-input v-model:value="ts.description" placeholder="Sheet 说明（可选）" size="small" />
              </a-descriptions-item>
            </a-descriptions>

            <!-- 字段映射表格 -->
            <a-table
              :columns="mappingTableColumns"
              :data-source="currentSheetTargetFields"
              row-key="name"
              :pagination="false"
              :scroll="{ y: 500 }"
              size="middle"
              style="margin-top: 12px"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'target_field'">
                  <div class="target-field-cell">
                    <span class="field-index">{{ record.index + 1 }}</span>
                    <span class="field-name">{{ record.name }}</span>
                    <a-tag v-if="getMappingInSheet(ts, record.name)" color="green" class="status-tag">
                      <CheckCircleOutlined /> 已配置
                    </a-tag>
                    <a-tag v-else color="default" class="status-tag">待配置</a-tag>
                  </div>
                </template>
                <template v-else-if="column.key === 'rule'">
                  <div class="rule-cell">
                    <template v-if="getMappingInSheet(ts, record.name)">
                      <a-tag :color="getFieldTypeColor(getMappingInSheet(ts, record.name)?.field_type)">
                        {{ getFieldTypeLabel(getMappingInSheet(ts, record.name)?.field_type) }}
                      </a-tag>
                      <span class="rule-desc">
                        {{ getMappingDescription(getMappingInSheet(ts, record.name)) }}
                      </span>
                    </template>
                    <span v-else class="text-gray">暂无映射规则</span>
                  </div>
                </template>
                <template v-else-if="column.key === 'action'">
                  <a-space>
                    <a-button type="link" size="small" @click="openFieldConfig(record)">
                      <EditOutlined /> 配置
                    </a-button>
                    <a-button
                      v-if="getMappingInSheet(ts, record.name)"
                      type="link" danger size="small"
                      @click="removeFieldInSheet(ts, record.name)"
                    >
                      清除
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-tab-pane>
        </a-tabs>
      </a-card>

      <!-- Legacy 单 Sheet 模式：单一表格 -->
      <a-card v-else class="mapping-table-card" :bordered="false">
        <a-alert
          v-if="!legacyFields.length && !formData.target_sheet"
          type="warning"
          show-icon
          message="请先在步骤 1 勾选至少一个目标 Sheet，或继续以单 Sheet 模式手动配置"
          style="margin-bottom: 12px"
        />
        <a-table
          :columns="mappingTableColumns"
          :data-source="currentSheetTargetFields"
          row-key="name"
          :pagination="false"
          :scroll="{ y: 600 }"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'target_field'">
              <div class="target-field-cell">
                <span class="field-index">{{ record.index + 1 }}</span>
                <span class="field-name">{{ record.name }}</span>
                <a-tag v-if="getLegacyMapping(record.name)" color="green" class="status-tag">
                  <CheckCircleOutlined /> 已配置
                </a-tag>
                <a-tag v-else color="default" class="status-tag">待配置</a-tag>
              </div>
            </template>
            <template v-else-if="column.key === 'rule'">
              <div class="rule-cell">
                <template v-if="getLegacyMapping(record.name)">
                  <a-tag :color="getFieldTypeColor(getLegacyMapping(record.name)?.field_type)">
                    {{ getFieldTypeLabel(getLegacyMapping(record.name)?.field_type) }}
                  </a-tag>
                  <span class="rule-desc">{{ getMappingDescription(getLegacyMapping(record.name)) }}</span>
                </template>
                <span v-else class="text-gray">暂无映射规则</span>
              </div>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="openFieldConfig(record)">
                  <EditOutlined /> 配置
                </a-button>
                <a-button
                  v-if="getLegacyMapping(record.name)"
                  type="link" danger size="small"
                  @click="removeLegacyMapping(record.name)"
                >清除</a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>

    <!-- ============ Step 2: 血缘配置 ============ -->
    <div v-show="currentStep === 2" class="lineage-container">
      <a-card class="mapping-toolbar" :bordered="false">
        <div class="toolbar-content">
          <a-space>
            <a-button @click="currentStep = 1">
              <template #icon><LeftOutlined /></template>
              上一步
            </a-button>
          </a-space>
          <a-space>
            <a-tag color="blue">目标 Sheet: {{ formData.target_sheets.length }}</a-tag>
            <a-tag color="purple">Sheet 血缘: {{ formData.sheet_lineages.length }}</a-tag>
            <a-tag color="gold">字段血缘: {{ formData.field_lineages.length }}</a-tag>
          </a-space>
        </div>
      </a-card>

      <a-card :bordered="false">
        <a-alert
          v-if="uiMode === 'legacy_single'"
          type="info"
          show-icon
          message="当前为 Legacy 单 Sheet 模式，不支持血缘配置。返回上一步升级为多 Sheet 模式后可用。"
          style="margin-bottom: 16px"
        />
        <LineageDesigner
          v-else
          :target-sheets="formData.target_sheets"
          :sheet-lineages="formData.sheet_lineages"
          :field-lineages="formData.field_lineages"
          @update:sheetLineages="val => (formData.sheet_lineages = val as any)"
          @update:fieldLineages="val => (formData.field_lineages = val as any)"
        />
      </a-card>
    </div>

    <!-- 字段配置抽屉 -->
    <a-drawer
      v-model:open="drawerVisible"
      title="配置字段映射规则"
      width="640"
      :mask-closable="false"
    >
      <div v-if="currentEditingTarget" class="drawer-header-info">
        <p>
          当前 Sheet: <strong>{{ activeSheetName || '(单 Sheet)' }}</strong>
          <span style="margin: 0 12px; color: var(--color-text-dim)">·</span>
          目标字段: <strong>{{ currentEditingTarget.name }}</strong>
        </p>
      </div>

      <MappingRuleConfig
        v-if="drawerVisible && currentEditingTarget"
        :initial-data="currentEditingMapping"
        :source-fields="sourceFieldsForCurrent"
        :reference-sheets="referenceSheets"
        :upstream-sheets="upstreamSheetsForCurrent"
        @confirm="saveFieldConfig"
        @cancel="drawerVisible = false"
      />
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  LeftOutlined, RightOutlined,
  DeleteOutlined, PlusOutlined,
  ThunderboltOutlined, EditOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'
import { getFiles, type FileInfo } from '@/api/file'
import {
  getMapping,
  createMapping,
  updateMapping,
  parseFileFields,
  type MappingField,
  type MappingTargetSheet,
  type SheetLineageEdge,
  type FieldLineageEdge,
  type SheetInfo,
} from '@/api/processing'
import MappingRuleConfig from '@/components/processing/MappingRuleConfig.vue'
import LineageDesigner from '@/components/processing/LineageDesigner.vue'
import { topoSortSheets } from '@/composables/useSheetTopoSort'

// -------------------------------------------------------------------------
// 路由
// -------------------------------------------------------------------------
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)
const mappingId = computed(() => Number(route.params.id) || 0)

// -------------------------------------------------------------------------
// 步骤条
// -------------------------------------------------------------------------
const currentStep = ref(0)
const stepItems = [
  { title: '文件选择', description: '基本信息 + 目标 Sheet 种子' },
  { title: '字段映射', description: '按 Sheet 配置字段' },
  { title: '血缘配置', description: 'Sheet 与字段血缘' },
]

// -------------------------------------------------------------------------
// 状态
// -------------------------------------------------------------------------
const saving = ref(false)
const formRef = ref()

const fileList = ref<FileInfo[]>([])
const sourceSheets = ref<SheetInfo[]>([])
const referenceSheets = ref<SheetInfo[]>([])
const templateSheets = ref<SheetInfo[]>([])

// Step 0 多选的目标 Sheet 名（作为 target_sheets 种子）
const selectedTemplateSheetNames = ref<string[]>([])

interface FormState {
  name: string
  description: string
  source_file: number | undefined
  source_sheet: string
  reference_file: number | undefined
  reference_sheet: string
  target_template: number | undefined
  target_sheet: string                 // legacy 单 sheet 字段
  status: string
  // legacy 字段集合（target_sheet_config 为 null 的老数据）
  fields: MappingField[]
  // 多 Sheet
  target_sheets: MappingTargetSheet[]
  sheet_lineages: SheetLineageEdge[]
  field_lineages: FieldLineageEdge[]
}

const formData = reactive<FormState>({
  name: '',
  description: '',
  source_file: undefined,
  source_sheet: '',
  reference_file: undefined,
  reference_sheet: '',
  target_template: undefined,
  target_sheet: '',
  status: 'draft',
  fields: [],
  target_sheets: [],
  sheet_lineages: [],
  field_lineages: [],
})

// 抽屉状态
const drawerVisible = ref(false)
const currentEditingTarget = ref<{ name: string; index: number } | null>(null)
const activeSheetName = ref<string>('')

// -------------------------------------------------------------------------
// 表单校验规则
// -------------------------------------------------------------------------
const formRules = {
  name: [{ required: true, message: '请输入配置名称' }],
  source_file: [{ required: true, message: '请选择源数据文件' }],
  source_sheet: [{ required: true, message: '请选择源文件工作表' }],
  target_template: [{ required: true, message: '请选择目标模板文件' }],
}

const mappingTableColumns = [
  { title: '目标字段', key: 'target_field', width: 260 },
  { title: '映射规则', key: 'rule' },
  { title: '操作', key: 'action', width: 150, fixed: 'right' },
]

// -------------------------------------------------------------------------
// 模式判定
// -------------------------------------------------------------------------
const uiMode = computed<'legacy_single' | 'multi_sheet'>(() =>
  formData.target_sheets.length === 0 ? 'legacy_single' : 'multi_sheet'
)

// Legacy 模式下的 fields（仅显示）
const legacyFields = computed(() => formData.fields)

// -------------------------------------------------------------------------
// 计算属性：当前选中 Sheet 的各种派生信息
// -------------------------------------------------------------------------
const currentSheet = computed<MappingTargetSheet | null>(() => {
  if (uiMode.value === 'legacy_single') return null
  return formData.target_sheets.find(s => s.sheet_name === activeSheetName.value) || null
})

// 当前 Sheet 对应的"模板目标字段"列表（从 templateSheets 里取）
const currentSheetTargetFields = computed<{ name: string; index: number }[]>(() => {
  const name =
    uiMode.value === 'legacy_single'
      ? formData.target_sheet
      : currentSheet.value?.sheet_name || ''
  if (!name) return []
  const tpl = templateSheets.value.find(s => s.sheet_name === name)
  return tpl?.fields || []
})

// 当前 Sheet 使用的源字段列表（支持 ts.source_sheet 覆盖默认）
const sourceFieldsForCurrent = computed<{ name: string; index: number }[]>(() => {
  const srcName =
    uiMode.value === 'legacy_single'
      ? formData.source_sheet
      : currentSheet.value?.source_sheet || formData.source_sheet
  if (!srcName) return []
  const s = sourceSheets.value.find(x => x.sheet_name === srcName)
  return s?.fields || []
})

// 当前 Sheet 在拓扑血缘中可选的上游 Sheet（用于 cross_sheet_ref / computed 跨 sheet 占位符）
const upstreamSheetsForCurrent = computed<MappingTargetSheet[]>(() => {
  if (uiMode.value === 'legacy_single' || !currentSheet.value) return []
  const cur = currentSheet.value
  const ancestors = computeAncestors(formData.sheet_lineages, cur.sheet_name)
  if (ancestors.length > 0) {
    return formData.target_sheets.filter(s => ancestors.includes(s.sheet_name))
  }
  // 无血缘定义时，退化为"除自己外的所有目标 Sheet"
  return formData.target_sheets.filter(s => s.sheet_name !== cur.sheet_name)
})

// 当前正在编辑的字段（给抽屉用）
const currentEditingMapping = computed<Partial<MappingField>>(() => {
  if (!currentEditingTarget.value) return {}
  if (uiMode.value === 'legacy_single') {
    return formData.fields.find(f => f.target_field === currentEditingTarget.value!.name) || {}
  }
  if (!currentSheet.value) return {}
  return currentSheet.value.fields.find(f => f.target_field === currentEditingTarget.value!.name) || {}
})

const mappedCount = computed(() => {
  if (uiMode.value === 'legacy_single') return formData.fields.length
  return currentSheet.value?.fields.length || 0
})
const unmappedCount = computed(() => currentSheetTargetFields.value.length - mappedCount.value)

const canProceedToMapping = computed(() => {
  return (
    formData.source_file &&
    formData.source_sheet &&
    formData.target_template &&
    templateSheets.value.length > 0
  )
})

const canProceedToLineage = computed(() => uiMode.value === 'multi_sheet' && formData.target_sheets.length > 0)

// -------------------------------------------------------------------------
// 工具：根据 sheet_lineages 计算 target sheet 的所有祖先
// -------------------------------------------------------------------------
function computeAncestors(lineages: SheetLineageEdge[], target: string): string[] {
  const parents = new Map<string, string[]>()
  for (const sl of lineages) {
    if (!sl.upstream || !sl.downstream) continue
    const arr = parents.get(sl.downstream) || []
    arr.push(sl.upstream)
    parents.set(sl.downstream, arr)
  }
  const result = new Set<string>()
  const stack = [target]
  const visited = new Set<string>()
  while (stack.length) {
    const cur = stack.pop()!
    if (visited.has(cur)) continue
    visited.add(cur)
    for (const p of parents.get(cur) || []) {
      if (!result.has(p)) {
        result.add(p)
        stack.push(p)
      }
    }
  }
  return Array.from(result)
}

// -------------------------------------------------------------------------
// 文件 / Sheet 变更
// -------------------------------------------------------------------------
function filterOption(input: string, option: any) {
  return option.children[0].children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

async function loadFiles() {
  try {
    const res = await getFiles({ page_size: 1000 })
    const data: any = (res.data as any)?.data || res.data
    fileList.value = data.results || []
  } catch (error) {
    console.error('加载文件列表失败:', error)
  }
}

async function parseFields(fileId: number): Promise<SheetInfo[]> {
  try {
    const res = await parseFileFields(fileId)
    return res.data.data?.sheets || []
  } catch (error) {
    console.error('解析文件字段失败:', error)
    return []
  }
}

async function handleSourceFileChange(fileId: number) {
  formData.source_sheet = ''
  sourceSheets.value = []
  if (fileId) {
    sourceSheets.value = await parseFields(fileId)
    const first = sourceSheets.value[0]
    if (sourceSheets.value.length === 1 && first) {
      formData.source_sheet = first.sheet_name
    }
  }
}

async function handleReferenceFileChange(fileId: number | undefined) {
  formData.reference_sheet = ''
  referenceSheets.value = []
  if (fileId) {
    referenceSheets.value = await parseFields(fileId)
    const first = referenceSheets.value[0]
    if (referenceSheets.value.length === 1 && first) {
      formData.reference_sheet = first.sheet_name
    }
  }
}

async function handleTargetFileChange(fileId: number) {
  formData.target_sheet = ''
  templateSheets.value = []
  selectedTemplateSheetNames.value = []
  if (fileId) {
    templateSheets.value = await parseFields(fileId)
  }
}

// -------------------------------------------------------------------------
// 从 Step 0 的勾选生成 target_sheets 种子（Req 13.1）
// -------------------------------------------------------------------------
function seedTargetSheetsFromTemplate() {
  const existingByName = new Map(formData.target_sheets.map(t => [t.sheet_name, t]))
  const picks = selectedTemplateSheetNames.value

  // 场景 A：勾了 2+ 个 → 进入多 Sheet 模式
  if (picks.length >= 2) {
    formData.target_sheets = picks.map((name, i) => {
      const existed = existingByName.get(name)
      return existed
        ? { ...existed, sort_order: i }
        : {
            sheet_name: name,
            display_name: '',
            description: '',
            status: 'draft' as const,
            source_sheet: '',
            sort_order: i,
            fields: [],
          }
    })
    activeSheetName.value = formData.target_sheets[0]?.sheet_name || ''
    // legacy 单 Sheet 字段清掉，避免混淆
    formData.target_sheet = ''
    formData.fields = []
  } else if (picks.length === 1) {
    // 场景 B：勾了 1 个 → 保持 Legacy 单 Sheet 模式
    const name = picks[0] as string
    formData.target_sheet = name
    formData.target_sheets = []
    activeSheetName.value = ''
    // 如果 legacy fields 里的 target_field 已经不在新 sheet 里了，保留也没问题（后端按名称匹配，用户可再编辑）
  } else {
    // 场景 C：一个都没勾 → 允许手动在 Step 1 添加 target sheet
    formData.target_sheet = ''
  }
}

function goToMapping() {
  if (!canProceedToMapping.value) {
    message.warning('请先完成文件选择')
    return
  }
  seedTargetSheetsFromTemplate()
  currentStep.value = 1
}

// -------------------------------------------------------------------------
// Tabs 编辑事件（新建 / 删除 Sheet）
// -------------------------------------------------------------------------
function onTabEdit(targetKey: string | MouseEvent, action: 'add' | 'remove') {
  if (action === 'add') {
    addCustomSheet()
  } else if (action === 'remove' && typeof targetKey === 'string') {
    removeSheet(targetKey)
  }
}

function addCustomSheet() {
  // 从尚未加入 target_sheets 的 templateSheets 中挑第一个，否则弹输入
  const used = new Set(formData.target_sheets.map(s => s.sheet_name))
  const unused = templateSheets.value.find(s => !used.has(s.sheet_name))
  const name = unused?.sheet_name || prompt('请输入新 Sheet 名称：')?.trim() || ''
  if (!name) return
  if (used.has(name)) {
    message.error(`Sheet "${name}" 已存在`)
    return
  }
  formData.target_sheets.push({
    sheet_name: name,
    display_name: '',
    description: '',
    status: 'draft',
    source_sheet: '',
    sort_order: formData.target_sheets.length,
    fields: [],
  })
  activeSheetName.value = name
}

function removeSheet(name: string) {
  if (formData.target_sheets.length <= 1) {
    message.warning('至少保留一个目标 Sheet')
    return
  }
  if (!confirm(`确定删除 Sheet "${name}" 及其字段映射？`)) return
  const idx = formData.target_sheets.findIndex(s => s.sheet_name === name)
  if (idx >= 0) formData.target_sheets.splice(idx, 1)
  formData.target_sheets.forEach((s, i) => (s.sort_order = i))
  // 同步清理指向它的血缘
  formData.sheet_lineages = formData.sheet_lineages.filter(
    sl => sl.upstream !== name && sl.downstream !== name
  )
  formData.field_lineages = formData.field_lineages.filter(
    fl => fl.upstream_sheet !== name && fl.downstream_sheet !== name
  )
  if (activeSheetName.value === name) {
    activeSheetName.value = formData.target_sheets[0]?.sheet_name || ''
  }
}

// -------------------------------------------------------------------------
// 字段映射（多 Sheet / Legacy 双路径）
// -------------------------------------------------------------------------
function getMappingInSheet(ts: MappingTargetSheet, targetFieldName: string): MappingField | undefined {
  return ts.fields.find(f => f.target_field === targetFieldName)
}

function getLegacyMapping(targetFieldName: string): MappingField | undefined {
  return formData.fields.find(f => f.target_field === targetFieldName)
}

function removeFieldInSheet(ts: MappingTargetSheet, targetFieldName: string) {
  const idx = ts.fields.findIndex(f => f.target_field === targetFieldName)
  if (idx >= 0) {
    ts.fields.splice(idx, 1)
    ts.fields.forEach((f, i) => (f.sort_order = i))
  }
}

function removeLegacyMapping(targetFieldName: string) {
  const idx = formData.fields.findIndex(f => f.target_field === targetFieldName)
  if (idx >= 0) {
    formData.fields.splice(idx, 1)
    formData.fields.forEach((f, i) => (f.sort_order = i))
  }
}

function clearCurrentSheetFields() {
  if (uiMode.value === 'legacy_single') {
    formData.fields = []
  } else if (currentSheet.value) {
    currentSheet.value.fields = []
  }
}

function openFieldConfig(targetField: { name: string; index: number }) {
  currentEditingTarget.value = targetField
  drawerVisible.value = true
}

function saveFieldConfig(config: Partial<MappingField>) {
  if (!currentEditingTarget.value) return

  const baseSource = sourceFieldsForCurrent.value.find(f => f.name === config.source_field)

  const mapping: MappingField = {
    target_sheet_name: uiMode.value === 'multi_sheet' ? activeSheetName.value : '',
    source_field: config.source_field || '',
    source_field_index: baseSource?.index ?? -1,
    reference_sheet: config.reference_sheet || '',
    reference_name_column: config.reference_name_column || '',
    reference_code_column: config.reference_code_column || '',
    reference_field: config.reference_name_column || '',
    reference_field_index: -1,
    target_field: currentEditingTarget.value.name,
    target_field_index: currentEditingTarget.value.index,
    field_type: (config.field_type as MappingField['field_type']) || 'direct',
    default_value: config.default_value || '',
    compute_expression: config.compute_expression || '',
    source_target_sheet_name: config.source_target_sheet_name || '',
    source_target_field: config.source_target_field || '',
    aggregation: (config.aggregation as MappingField['aggregation']) || '',
    transform_rule: config.transform_rule || null,
    sort_order: 0,
  }

  if (uiMode.value === 'legacy_single') {
    const existing = formData.fields.findIndex(f => f.target_field === mapping.target_field)
    if (existing >= 0) {
      mapping.sort_order = formData.fields[existing]?.sort_order ?? existing
      formData.fields[existing] = mapping
    } else {
      mapping.sort_order = formData.fields.length
      formData.fields.push(mapping)
    }
  } else {
    const ts = currentSheet.value
    if (!ts) return
    const existing = ts.fields.findIndex(f => f.target_field === mapping.target_field)
    if (existing >= 0) {
      mapping.sort_order = ts.fields[existing]?.sort_order ?? existing
      ts.fields[existing] = mapping
    } else {
      mapping.sort_order = ts.fields.length
      ts.fields.push(mapping)
    }
  }

  drawerVisible.value = false
  currentEditingTarget.value = null
  message.success('映射配置已保存')
}

// 智能匹配：按名称匹配 source→target
function autoMatch() {
  const src = sourceFieldsForCurrent.value
  const tgt = currentSheetTargetFields.value
  if (!src.length || !tgt.length) {
    message.warning('当前 Sheet 没有源字段或目标字段')
    return
  }

  const matches: MappingField[] = []
  src.forEach(sf => {
    const m = tgt.find(tf =>
      tf.name === sf.name ||
      tf.name.toLowerCase() === sf.name.toLowerCase() ||
      tf.name.includes(sf.name) || sf.name.includes(tf.name)
    )
    if (!m) return
    matches.push({
      target_sheet_name: uiMode.value === 'multi_sheet' ? activeSheetName.value : '',
      source_field: sf.name,
      source_field_index: sf.index,
      reference_sheet: '',
      reference_name_column: '',
      reference_code_column: '',
      reference_field: '',
      reference_field_index: -1,
      target_field: m.name,
      target_field_index: m.index,
      field_type: 'direct',
      default_value: '',
      compute_expression: '',
      source_target_sheet_name: '',
      source_target_field: '',
      aggregation: '',
      transform_rule: null,
      sort_order: matches.length,
    })
  })

  if (uiMode.value === 'legacy_single') {
    formData.fields = matches
  } else if (currentSheet.value) {
    currentSheet.value.fields = matches
  }
  message.success(`智能匹配完成，共 ${matches.length} 个字段`)
}

// Legacy → 多 Sheet 升级（Req 17.6）
function migrateLegacyToMultiSheet() {
  if (!formData.target_sheet) {
    message.warning('当前没有目标 Sheet 名，无法升级')
    return
  }
  const name = formData.target_sheet
  if (formData.target_sheets.find(s => s.sheet_name === name)) {
    message.warning('多 Sheet 列表已存在该 Sheet')
    return
  }
  formData.target_sheets.push({
    sheet_name: name,
    display_name: '',
    description: '',
    status: 'draft',
    source_sheet: formData.source_sheet,
    sort_order: 0,
    fields: formData.fields.map((f, i) => ({
      ...f,
      target_sheet_name: name,
      sort_order: i,
    })),
  })
  formData.fields = []
  formData.target_sheet = ''
  activeSheetName.value = name
  message.success('已升级为多 Sheet 模式，可继续在血缘步骤中添加更多 Sheet')
}

// -------------------------------------------------------------------------
// 映射展示助手
// -------------------------------------------------------------------------
function getFieldTypeLabel(type: string | undefined): string {
  const map: Record<string, string> = {
    direct: '直接映射',
    lookup: '对照表转换',
    computed: '计算字段',
    default: '默认值',
    cross_sheet_ref: '跨 Sheet 引用',
    source_to_target: '直接映射',
    source_to_ref: '源→对照',
    ref_to_target: '对照→目标',
    source_ref_target: '对照表转换',
  }
  return map[type || ''] || type || ''
}

function getFieldTypeColor(type: string | undefined): string {
  const map: Record<string, string> = {
    direct: 'blue',
    lookup: 'purple',
    computed: 'orange',
    default: 'cyan',
    cross_sheet_ref: 'gold',
    source_to_target: 'blue',
    source_ref_target: 'purple',
  }
  return map[type || ''] || 'default'
}

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
    case 'cross_sheet_ref': {
      const agg = mapping.aggregation ? `[${mapping.aggregation}]` : ''
      return `${mapping.source_target_sheet_name}.${mapping.source_target_field} ${agg}`.trim()
    }
    default:
      return mapping.source_field || ''
  }
}

function tabStatusColor(status: string | undefined): string {
  return status === 'ready' ? 'green' : status === 'disabled' ? 'default' : 'orange'
}

// -------------------------------------------------------------------------
// 保存
// -------------------------------------------------------------------------
async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    currentStep.value = 0
    message.warning('请完成基本信息填写')
    return
  }

  // 合法性检查
  if (uiMode.value === 'multi_sheet') {
    const anyFields = formData.target_sheets.some(s => s.fields.length > 0)
    if (!anyFields) {
      message.warning('请至少为一个目标 Sheet 配置字段映射')
      return
    }
  } else {
    if (formData.fields.length === 0) {
      message.warning('请至少添加一个字段映射')
      return
    }
  }

  saving.value = true
  try {
    const payload: any = {
      name: formData.name,
      description: formData.description,
      source_file: formData.source_file,
      source_sheet: formData.source_sheet,
      reference_file: formData.reference_file || undefined,
      reference_sheet: formData.reference_sheet || undefined,
      target_template: formData.target_template,
      target_sheet: formData.target_sheet,
      status: formData.status,
    }

    if (uiMode.value === 'legacy_single') {
      payload.fields = formData.fields.map((f, i) => ({ ...f, sort_order: i }))
    } else {
      payload.target_sheets = formData.target_sheets.map((ts, i) => ({
        ...ts,
        sort_order: i,
        fields: ts.fields.map((f, j) => ({
          ...f,
          target_sheet_name: ts.sheet_name,
          sort_order: j,
        })),
      }))
      payload.sheet_lineages = formData.sheet_lineages.map(sl => ({
        upstream: sl.upstream,
        downstream: sl.downstream,
        relation_type: sl.relation_type,
        description: sl.description || '',
        join_keys: sl.join_keys || null,
      }))
      payload.field_lineages = formData.field_lineages.map(fl => ({
        upstream_sheet: fl.upstream_sheet,
        upstream_field: fl.upstream_field,
        downstream_sheet: fl.downstream_sheet,
        downstream_field: fl.downstream_field,
        transform: fl.transform || 'direct',
        note: fl.note || '',
      }))
    }

    let resp: any
    if (isEdit.value) {
      resp = await updateMapping(mappingId.value, payload)
      message.success('配置更新成功')
    } else {
      resp = await createMapping(payload)
      message.success('配置创建成功')
    }

    // 后端返回的 warnings[] 提醒（Req 3.2 / 4.2 / 6.3）
    const warnings: any[] = (resp?.data && resp.data.warnings) || []
    warnings.forEach(w => {
      const label = typeof w === 'string' ? w : JSON.stringify(w)
      message.warning(label, 6)
    })

    router.push('/processing/mappings')
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

// -------------------------------------------------------------------------
// 加载现有配置（编辑模式）
// -------------------------------------------------------------------------
async function loadMapping() {
  if (!isEdit.value) return

  try {
    const res = await getMapping(mappingId.value)
    const data: any = (res.data as any)?.data ?? res.data
    if (!data || typeof data !== 'object') {
      message.error('加载配置失败: 响应格式异常')
      return
    }

    formData.name = data.name ?? ''
    formData.description = data.description ?? ''
    formData.source_file = data.source_file ?? undefined
    formData.source_sheet = data.source_sheet ?? ''
    formData.reference_file = data.reference_file ?? undefined
    formData.reference_sheet = data.reference_sheet ?? ''
    formData.target_template = data.target_template ?? undefined
    formData.target_sheet = data.target_sheet ?? ''
    formData.status = data.status ?? 'draft'

    // legacy 字段：只有 target_sheet_config 为 null 的才算 legacy
    const allFields: MappingField[] = Array.isArray(data.fields) ? data.fields : []
    formData.fields = allFields.filter(f => !f.target_sheet_config)

    // 多 Sheet
    formData.target_sheets = Array.isArray(data.target_sheets) ? data.target_sheets : []

    // 血缘：后端返回时 upstream/downstream 是 id + 名称兼存；前端内部用名称
    const rawSL: any[] = Array.isArray(data.sheet_lineages) ? data.sheet_lineages : []
    formData.sheet_lineages = rawSL.map(sl => ({
      upstream: sl.upstream_name || sl.upstream || '',
      downstream: sl.downstream_name || sl.downstream || '',
      relation_type: sl.relation_type || 'derived',
      description: sl.description || '',
      join_keys: sl.join_keys || null,
    }))

    const rawFL: any[] = Array.isArray(data.field_lineages) ? data.field_lineages : []
    formData.field_lineages = rawFL.map(fl => ({
      upstream_sheet: fl.upstream_sheet_name || fl.upstream_sheet || '',
      upstream_field: fl.upstream_field,
      downstream_sheet: fl.downstream_sheet_name || fl.downstream_sheet || '',
      downstream_field: fl.downstream_field,
      transform: fl.transform || 'direct',
      note: fl.note || '',
    }))

    // 预选 Step 0 的多选勾选
    if (formData.target_sheets.length > 0) {
      selectedTemplateSheetNames.value = formData.target_sheets.map(s => s.sheet_name)
      activeSheetName.value = formData.target_sheets[0]?.sheet_name || ''
    } else if (formData.target_sheet) {
      selectedTemplateSheetNames.value = [formData.target_sheet]
    }

    // 解析相关工作表
    if (formData.source_file) sourceSheets.value = await parseFields(formData.source_file)
    if (formData.reference_file) referenceSheets.value = await parseFields(formData.reference_file)
    if (formData.target_template) templateSheets.value = await parseFields(formData.target_template)
  } catch (error) {
    console.error('加载配置失败:', error)
    message.error('加载配置失败')
  }
}

// 保证 activeSheetName 始终指向 target_sheets 中存在的一项
watch(
  () => formData.target_sheets.map(s => s.sheet_name).join(','),
  names => {
    if (!names) {
      activeSheetName.value = ''
      return
    }
    if (!formData.target_sheets.some(s => s.sheet_name === activeSheetName.value)) {
      activeSheetName.value = formData.target_sheets[0]?.sheet_name || ''
    }
  }
)

// 消除 topoSortSheets 未使用告警（保留导入以便将来扩展）
void topoSortSheets

onMounted(async () => {
  await loadFiles()
  await loadMapping()
})
</script>

<style scoped>
.mapping-edit {
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
  font-weight: 700;
  font-family: 'Fira Code', monospace;
  color: var(--color-text);
}

.steps-card {
  margin-bottom: 16px;
}

.form-card {
  margin-bottom: 16px;
}

.help-tip {
  font-size: 12px;
  color: var(--color-text-dim, #999);
  margin-top: 4px;
}

.mapping-toolbar {
  margin-bottom: 16px;
}

.mapping-toolbar :deep(.ant-card-body) {
  padding: 12px 24px;
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mapping-table-card {
  margin-bottom: 16px;
}

.sheet-props {
  margin-top: 8px;
}

.mono {
  font-family: 'Fira Code', monospace;
}

.target-field-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-text-muted, #666);
  flex-shrink: 0;
  font-family: 'Fira Code', monospace;
}

.field-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text);
}

.status-tag {
  flex-shrink: 0;
}

.rule-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-desc {
  color: var(--color-text-muted, #666);
  font-size: 13px;
}

.text-gray {
  color: var(--color-text-dim, #999);
  font-size: 13px;
}

.drawer-header-info {
  padding: 0 0 16px;
  border-bottom: 1px solid var(--color-border, #f0f0f0);
  margin-bottom: 16px;
  color: var(--color-text-muted);
}

.drawer-header-info strong {
  color: var(--color-text);
  font-family: 'Fira Code', monospace;
}

.lineage-container {
  margin-top: 0;
}
</style>
