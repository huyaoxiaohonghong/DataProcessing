<template>
  <div class="menu-page">
    <div class="header-actions">
      <h2 class="page-title">菜单管理</h2>
      <div class="actions">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索菜单名称..."
          style="width: 250px"
          @search="handleSearch"
        />
        <a-button type="primary" @click="showAddModal()">
          <PlusOutlined /> 新增菜单
        </a-button>
      </div>
    </div>

    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="menuList"
        :loading="loading"
        :pagination="false"
        rowKey="id"
        :expandable="{ defaultExpandAllRows: true }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'icon'">
            <span v-if="record.icon">{{ record.icon }}</span>
            <span v-else class="text-muted">-</span>
          </template>
          <template v-else-if="column.key === 'menu_type'">
            <a-tag :color="getTypeColor(record.menu_type)">
              {{ record.menu_type_display }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.status ? 'success' : 'default'">
              {{ record.status ? '正常' : '停用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'visible'">
            <a-tag :color="record.visible ? 'blue' : 'default'">
              {{ record.visible ? '显示' : '隐藏' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="showAddModal(record)">
                <PlusOutlined /> 新增
              </a-button>
              <a-button type="link" size="small" @click="showEditModal(record)">
                <EditOutlined /> 编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个菜单吗？"
                @confirm="handleDelete(record)"
              >
                <a-button type="link" danger size="small">
                  <DeleteOutlined /> 删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 新增/编辑菜单弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑菜单' : '新增菜单'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
      :width="650"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 5 }"
        :wrapper-col="{ span: 17 }"
      >
        <a-form-item label="上级菜单" name="parent">
          <a-tree-select
            v-model:value="formData.parent"
            placeholder="请选择上级菜单"
            allow-clear
            :tree-data="parentTreeData"
            :field-names="{ label: 'name', value: 'id', children: 'children' }"
          />
        </a-form-item>
        
        <a-form-item label="菜单类型" name="menu_type">
          <a-radio-group v-model:value="formData.menu_type">
            <a-radio-button v-for="type in menuTypes" :key="type.value" :value="type.value">
              {{ type.label }}
            </a-radio-button>
          </a-radio-group>
        </a-form-item>
        
        <a-form-item label="菜单名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入菜单名称" />
        </a-form-item>
        
        <a-form-item v-if="formData.menu_type !== 'button'" label="路由路径" name="path">
          <a-input v-model:value="formData.path" placeholder="请输入路由路径" />
        </a-form-item>
        
        <a-form-item v-if="formData.menu_type === 'menu'" label="组件路径" name="component">
          <a-input v-model:value="formData.component" placeholder="请输入组件路径" />
        </a-form-item>
        
        <a-form-item v-if="formData.menu_type !== 'button'" label="图标" name="icon">
          <a-input v-model:value="formData.icon" placeholder="请输入图标名称" />
        </a-form-item>
        
        <a-form-item v-if="formData.menu_type === 'button'" label="权限标识" name="permission">
          <a-input v-model:value="formData.permission" placeholder="如：system:user:add" />
        </a-form-item>
        
        <a-form-item label="排序" name="sort">
          <a-input-number v-model:value="formData.sort" :min="0" style="width: 100%" />
        </a-form-item>
        
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="状态" name="status" :label-col="{ span: 10 }" :wrapper-col="{ span: 14 }">
              <a-switch v-model:checked="formData.status" checked-children="正常" un-checked-children="停用" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="显示" name="visible" :label-col="{ span: 10 }" :wrapper-col="{ span: 14 }">
              <a-switch v-model:checked="formData.visible" checked-children="显示" un-checked-children="隐藏" />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-form-item label="备注" name="remark">
          <a-textarea v-model:value="formData.remark" :rows="2" placeholder="请输入备注" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message, type FormInstance } from 'ant-design-vue'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import {
  getMenuTree,
  getMenuTypes,
  createMenu,
  updateMenu,
  deleteMenu,
  type Menu,
  type MenuType
} from '@/api/system'

const loading = ref(false)
const menuList = ref<Menu[]>([])
const searchText = ref('')

const columns = [
  { title: '菜单名称', dataIndex: 'name', width: 200 },
  { title: '图标', key: 'icon', width: 80 },
  { title: '类型', key: 'menu_type', width: 100 },
  { title: '路由路径', dataIndex: 'path', width: 180 },
  { title: '权限标识', dataIndex: 'permission', width: 150 },
  { title: '排序', dataIndex: 'sort', width: 80 },
  { title: '状态', key: 'status', width: 80 },
  { title: '显示', key: 'visible', width: 80 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' },
]

// 弹窗相关
const modalVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const menuTypes = ref<MenuType[]>([])

const formData = reactive({
  name: '',
  parent: null as number | null,
  path: '',
  component: '',
  icon: '',
  menu_type: 'menu',
  permission: '',
  sort: 0,
  status: true,
  visible: true,
  cache: true,
  remark: ''
})

const formRules = {
  name: [{ required: true, message: '请输入菜单名称' }],
  menu_type: [{ required: true, message: '请选择菜单类型' }]
}

const parentTreeData = computed(() => {
  // 过滤掉按钮类型，只保留目录和菜单
  function filterTree(items: Menu[]): any[] {
    return items
      .filter(item => item.menu_type !== 'button')
      .map(item => ({
        ...item,
        children: item.children ? filterTree(item.children) : []
      }))
  }
  return filterTree(menuList.value)
})

onMounted(() => {
  fetchMenus()
  fetchMenuTypes()
})

async function fetchMenus() {
  loading.value = true
  try {
    const res = await getMenuTree()
    menuList.value = res.data.data
  } catch (error) {
    message.error('获取菜单列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchMenuTypes() {
  try {
    const res = await getMenuTypes()
    menuTypes.value = res.data.data
  } catch (error) {
    console.error('获取菜单类型失败', error)
  }
}

function handleSearch() {
  fetchMenus()
}

function getTypeColor(type: string) {
  const map: Record<string, string> = {
    directory: 'blue',
    menu: 'green',
    button: 'orange'
  }
  return map[type] || 'default'
}

function resetForm() {
  formData.name = ''
  formData.parent = null
  formData.path = ''
  formData.component = ''
  formData.icon = ''
  formData.menu_type = 'menu'
  formData.permission = ''
  formData.sort = 0
  formData.status = true
  formData.visible = true
  formData.cache = true
  formData.remark = ''
  editingId.value = null
}

function showAddModal(parentRecord?: Menu) {
  isEdit.value = false
  resetForm()
  if (parentRecord) {
    formData.parent = parentRecord.id
  }
  modalVisible.value = true
}

function showEditModal(record: Menu) {
  isEdit.value = true
  editingId.value = record.id
  formData.name = record.name
  formData.parent = record.parent
  formData.path = record.path || ''
  formData.component = record.component || ''
  formData.icon = record.icon || ''
  formData.menu_type = record.menu_type
  formData.permission = record.permission || ''
  formData.sort = record.sort
  formData.status = record.status
  formData.visible = record.visible
  formData.cache = record.cache
  formData.remark = record.remark || ''
  modalVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  
  submitting.value = true
  try {
    if (isEdit.value && editingId.value) {
      await updateMenu(editingId.value, formData)
      message.success('更新成功')
    } else {
      await createMenu(formData)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchMenus()
  } catch (error: any) {
    message.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(record: Menu) {
  try {
    const res = await deleteMenu(record.id)
    if (res.data.code === 200) {
      message.success('删除成功')
      fetchMenus()
    } else {
      message.error(res.data.message || '删除失败')
    }
  } catch (error: any) {
    message.error(error.response?.data?.message || '删除失败')
  }
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

.text-muted {
  color: var(--color-text-dim);
}
</style>
