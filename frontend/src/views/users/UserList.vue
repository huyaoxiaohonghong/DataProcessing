<template>
  <div class="user-page">
    <div class="header-actions">
      <h2 class="page-title">用户管理</h2>
      <div class="actions">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索用户名、邮箱、手机号..."
          style="width: 280px"
          @search="handleSearch"
        />
        <a-select
          v-model:value="filterRole"
          placeholder="筛选角色"
          style="width: 120px"
          allowClear
          @change="handleSearch"
        >
          <a-select-option v-for="role in roleOptions" :key="role.value" :value="role.value">
            {{ role.label }}
          </a-select-option>
        </a-select>
        <a-button type="primary" @click="showAddModal">
          <PlusOutlined /> 新增用户
        </a-button>
      </div>
    </div>

    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="userList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">
            <a-tag :color="getRoleColor(record.role)">
              {{ record.role_display }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.is_active ? 'success' : 'default'">
              {{ record.is_active ? '正常' : '禁用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="showEditModal(record)">
                <EditOutlined /> 编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个用户吗？"
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

    <!-- 新增/编辑用户弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      @ok="handleSubmit"
      :confirm-loading="submitting"
      :width="600"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="formData.username" placeholder="请输入用户名" :disabled="isEdit" />
        </a-form-item>
        
        <a-form-item label="密码" name="password">
          <a-input-password v-model:value="formData.password" :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'" />
        </a-form-item>
        
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="formData.email" placeholder="请输入邮箱" />
        </a-form-item>
        
        <a-form-item label="手机号" name="phone">
          <a-input v-model:value="formData.phone" placeholder="请输入手机号" />
        </a-form-item>
        
        <a-form-item label="姓名" name="first_name">
          <a-input v-model:value="formData.first_name" placeholder="请输入姓名" />
        </a-form-item>
        
        <a-form-item label="角色" name="role">
          <a-select v-model:value="formData.role" placeholder="请选择角色">
            <a-select-option v-for="role in roleOptions" :key="role.value" :value="role.value">
              {{ role.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="部门" name="department">
          <a-select
            v-model:value="formData.department"
            placeholder="请选择部门"
            allowClear
            :options="departmentOptions"
          />
        </a-form-item>
        
        <a-form-item label="状态" name="is_active">
          <a-switch v-model:checked="formData.is_active" checked-children="正常" un-checked-children="禁用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message, type FormInstance } from 'ant-design-vue'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  getRoles,
  type UserManage,
  type RoleOption
} from '@/api/user'
import { getDepartmentSimple } from '@/api/system'

const loading = ref(false)
const userList = ref<UserManage[]>([])
const searchText = ref('')
const filterRole = ref<string | undefined>(undefined)
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const columns = [
  { title: '用户名', dataIndex: 'username', width: 120 },
  { title: '姓名', dataIndex: 'first_name', width: 100 },
  { title: '邮箱', dataIndex: 'email', width: 180 },
  { title: '手机号', dataIndex: 'phone', width: 130 },
  { title: '角色', key: 'role', width: 100 },
  { title: '部门', dataIndex: 'department_name', width: 120 },
  { title: '状态', key: 'status', width: 80 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 160, fixed: 'right' },
]

// 弹窗相关
const modalVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const roleOptions = ref<RoleOption[]>([])
const departmentOptions = ref<{ label: string; value: number }[]>([])

const formData = reactive({
  username: '',
  password: '',
  email: '',
  phone: '',
  first_name: '',
  role: 'viewer',
  department: null as number | null,
  is_active: true
})

const formRules = {
  username: [{ required: true, message: '请输入用户名' }],
  role: [{ required: true, message: '请选择角色' }]
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
  fetchDepartments()
})

async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUsers({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value,
      role: filterRole.value
    })
    const data = res.data?.data || res.data
    userList.value = data.results || []
    pagination.total = data.pagination?.total || data.count || 0
  } catch (error) {
    message.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchRoles() {
  try {
    const res = await getRoles()
    roleOptions.value = res.data.data
  } catch (error) {
    console.error('获取角色失败', error)
  }
}

async function fetchDepartments() {
  try {
    const res = await getDepartmentSimple()
    departmentOptions.value = res.data.data.map((item: any) => ({
      label: item.name,
      value: item.id
    }))
  } catch (error) {
    console.error('获取部门失败', error)
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchUsers()
}

function handleSearch() {
  pagination.current = 1
  fetchUsers()
}

function getRoleColor(role: string) {
  const map: Record<string, string> = {
    admin: 'red',
    operator: 'blue',
    viewer: 'green'
  }
  return map[role] || 'default'
}

function resetForm() {
  formData.username = ''
  formData.password = ''
  formData.email = ''
  formData.phone = ''
  formData.first_name = ''
  formData.role = 'viewer'
  formData.department = null
  formData.is_active = true
  editingId.value = null
}

function showAddModal() {
  isEdit.value = false
  resetForm()
  modalVisible.value = true
}

function showEditModal(record: UserManage) {
  isEdit.value = true
  editingId.value = record.id
  formData.username = record.username
  formData.password = ''
  formData.email = record.email || ''
  formData.phone = record.phone || ''
  formData.first_name = record.first_name || ''
  formData.role = record.role
  formData.department = record.department
  formData.is_active = record.is_active
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
    const data: any = { ...formData }
    if (!data.password) {
      delete data.password
    }
    
    if (isEdit.value && editingId.value) {
      await updateUser(editingId.value, data)
      message.success('更新成功')
    } else {
      await createUser(data)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchUsers()
  } catch (error: any) {
    message.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(record: UserManage) {
  try {
    const res = await deleteUser(record.id)
    if (res.data.code === 200) {
      message.success('删除成功')
      fetchUsers()
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
</style>
