<template>
  <div class="department-page">
    <div class="header-actions">
      <h2 class="page-title">部门管理</h2>
      <div class="actions">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索部门名称、编码..."
          style="width: 250px"
          @search="handleSearch"
        />
        <a-button type="primary" @click="showAddModal">
          <PlusOutlined /> 新增部门
        </a-button>
      </div>
    </div>

    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="departmentList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status ? 'success' : 'default'">
              {{ record.status ? '正常' : '停用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="showEditModal(record)">
                <EditOutlined /> 编辑
              </a-button>
              <a-popconfirm
                title="确定要删除这个部门吗？"
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

    <!-- 新增/编辑部门弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑部门' : '新增部门'"
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
        <a-form-item label="部门名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入部门名称" />
        </a-form-item>
        
        <a-form-item label="部门编码" name="code">
          <a-input v-model:value="formData.code" placeholder="请输入部门编码" />
        </a-form-item>
        
        <a-form-item label="上级部门" name="parent">
          <a-select
            v-model:value="formData.parent"
            placeholder="请选择上级部门"
            allowClear
            :options="parentOptions"
          />
        </a-form-item>
        
        <a-form-item label="负责人" name="leader">
          <a-input v-model:value="formData.leader" placeholder="请输入负责人" />
        </a-form-item>
        
        <a-form-item label="联系电话" name="phone">
          <a-input v-model:value="formData.phone" placeholder="请输入联系电话" />
        </a-form-item>
        
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="formData.email" placeholder="请输入邮箱" />
        </a-form-item>
        
        <a-form-item label="排序" name="sort">
          <a-input-number v-model:value="formData.sort" :min="0" style="width: 100%" />
        </a-form-item>
        
        <a-form-item label="状态" name="status">
          <a-switch v-model:checked="formData.status" checked-children="正常" un-checked-children="停用" />
        </a-form-item>
        
        <a-form-item label="备注" name="remark">
          <a-textarea v-model:value="formData.remark" :rows="3" placeholder="请输入备注" />
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
  getDepartments,
  getDepartmentSimple,
  createDepartment,
  updateDepartment,
  deleteDepartment,
  type Department
} from '@/api/system'

const loading = ref(false)
const departmentList = ref<Department[]>([])
const searchText = ref('')
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const columns = [
  { title: '部门名称', dataIndex: 'name', width: 150 },
  { title: '部门编码', dataIndex: 'code', width: 120 },
  { title: '上级部门', dataIndex: 'parent_name', width: 120 },
  { title: '负责人', dataIndex: 'leader', width: 100 },
  { title: '联系电话', dataIndex: 'phone', width: 130 },
  { title: '排序', dataIndex: 'sort', width: 80 },
  { title: '状态', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 180, fixed: 'right' },
]

// 弹窗相关
const modalVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingId = ref<number | null>(null)
const parentOptions = ref<{ label: string; value: number }[]>([])

const formData = reactive({
  name: '',
  code: '',
  parent: null as number | null,
  leader: '',
  phone: '',
  email: '',
  sort: 0,
  status: true,
  remark: ''
})

const formRules = {
  name: [{ required: true, message: '请输入部门名称' }],
  code: [{ required: true, message: '请输入部门编码' }]
}

onMounted(() => {
  fetchDepartments()
  fetchParentOptions()
})

async function fetchDepartments() {
  loading.value = true
  try {
    const res = await getDepartments({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value
    })
    departmentList.value = res.data.results
    pagination.total = res.data.count
  } catch (error) {
    message.error('获取部门列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchParentOptions() {
  try {
    const res = await getDepartmentSimple()
    parentOptions.value = res.data.data.map((item: any) => ({
      label: item.name,
      value: item.id
    }))
  } catch (error) {
    console.error('获取部门选项失败', error)
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchDepartments()
}

function handleSearch() {
  pagination.current = 1
  fetchDepartments()
}

function resetForm() {
  formData.name = ''
  formData.code = ''
  formData.parent = null
  formData.leader = ''
  formData.phone = ''
  formData.email = ''
  formData.sort = 0
  formData.status = true
  formData.remark = ''
  editingId.value = null
}

function showAddModal() {
  isEdit.value = false
  resetForm()
  modalVisible.value = true
}

function showEditModal(record: Department) {
  isEdit.value = true
  editingId.value = record.id
  formData.name = record.name
  formData.code = record.code
  formData.parent = record.parent
  formData.leader = record.leader || ''
  formData.phone = record.phone || ''
  formData.email = record.email || ''
  formData.sort = record.sort
  formData.status = record.status
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
      await updateDepartment(editingId.value, formData)
      message.success('更新成功')
    } else {
      await createDepartment(formData)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchDepartments()
    fetchParentOptions()
  } catch (error: any) {
    message.error(error.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(record: Department) {
  try {
    const res = await deleteDepartment(record.id)
    if (res.data.code === 200) {
      message.success('删除成功')
      fetchDepartments()
      fetchParentOptions()
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
