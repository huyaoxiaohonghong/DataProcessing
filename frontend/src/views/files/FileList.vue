<template>
  <div class="file-list-page">
    <div class="header-actions">
      <h2 class="page-title">文件管理</h2>
      <div class="actions">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索文件..."
          style="width: 250px"
          @search="handleSearch"
        />
        <a-button type="primary" @click="showUploadModal">
          <UploadOutlined /> 上传文件
        </a-button>
      </div>
    </div>

    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="fileList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="file-name">
              <file-icon :type="record.file_type" />
              <span>{{ record.name }}</span>
            </div>
          </template>
          
          <template v-else-if="column.key === 'size'">
            {{ record.file_size_display }}
          </template>
          
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              {{ record.status_display }}
            </a-tag>
          </template>
          
          <template v-else-if="column.key === 'is_public'">
              <a-tag :color="record.is_public ? 'green' : 'default'">
                  {{ record.is_public ? '公开' : '私有' }}
              </a-tag>
          </template>
          
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handlePreview(record)">
                <EyeOutlined /> 预览
              </a-button>
              <a-button type="link" size="small" @click="handleDownload(record)">
                <DownloadOutlined /> 下载
              </a-button>
              <a-popconfirm
                title="确定要删除这个文件吗？"
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

    <!-- 上传模态框 -->
    <a-modal
      v-model:open="uploadVisible"
      title="上传文件"
      @ok="handleUpload"
      :confirm-loading="uploading"
    >
      <a-form layout="vertical">
        <a-form-item label="选择文件" required>
          <a-upload-dragger
            v-model:fileList="uploadFileList"
            :before-upload="beforeUpload"
            :max-count="1"
            name="file"
          >
            <p class="ant-upload-drag-icon">
              <inbox-outlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此处上传</p>
          </a-upload-dragger>
        </a-form-item>
        
        <a-form-item label="描述">
          <a-textarea v-model:value="uploadForm.description" rows="3" />
        </a-form-item>
        
        <a-form-item>
          <a-checkbox v-model:checked="uploadForm.is_public">设为公开文件</a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 预览模态框 -->
    <a-modal
      v-model:open="previewVisible"
      :title="previewFile?.name"
      :footer="null"
      width="80%"
      :bodyStyle="{ maxHeight: '70vh', overflow: 'auto' }"
    >
      <div v-if="previewFile">
        <!-- 图片预览 -->
        <div v-if="isImageFile(previewFile.file_type)" class="preview-image">
          <img :src="getFileUrl(previewFile.file)" alt="preview" style="max-width: 100%; height: auto;" />
        </div>

        <!-- PDF 预览 -->
        <div v-else-if="isPdfFile(previewFile.file_type)" class="preview-pdf">
          <iframe :src="getFileUrl(previewFile.file)" style="width: 100%; height: 600px; border: none;"></iframe>
        </div>

        <!-- 文本文件预览 -->
        <div v-else-if="isTextFile(previewFile.file_type)" class="preview-text">
          <a-spin :spinning="previewLoading">
            <pre style="background: #f5f5f5; padding: 16px; border-radius: 4px; max-height: 500px; overflow: auto;">{{ previewContent }}</pre>
          </a-spin>
        </div>

        <!-- Excel 预览 -->
        <div v-else-if="isExcelFile(previewFile.file_type)" class="preview-excel">
          <a-spin :spinning="previewLoading">
            <a-table
              v-if="excelData.length > 0"
              :columns="excelColumns"
              :data-source="excelData"
              :pagination="{ pageSize: 20 }"
              :scroll="{ x: 'max-content' }"
              size="small"
            />
            <a-empty v-else description="无数据" />
          </a-spin>
        </div>

        <!-- 不支持预览 -->
        <div v-else class="preview-unsupported">
          <a-empty description="该文件类型暂不支持预览">
            <template #extra>
              <a-button type="primary" @click="handleDownload(previewFile)">
                <DownloadOutlined /> 下载文件
              </a-button>
            </template>
          </a-empty>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { message, type UploadProps } from 'ant-design-vue'
import {
  UploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  InboxOutlined,
  FileOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FileZipOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue'
import { getFiles, uploadFile, deleteFile, downloadFile, type FileInfo } from '@/api/file'
import apiClient from '@/api/client'
import * as XLSX from 'xlsx'

// 简单的文件图标组件
const FileIcon = (props: { type: string }) => {
  const type = props.type?.toLowerCase()
  if (['jpg', 'png', 'gif', 'jpeg', 'webp', 'svg'].includes(type)) return h(FileImageOutlined)
  if (['pdf'].includes(type)) return h(FilePdfOutlined)
  if (['doc', 'docx'].includes(type)) return h(FileWordOutlined)
  if (['xls', 'xlsx', 'csv'].includes(type)) return h(FileExcelOutlined)
  if (['zip', 'rar', '7z'].includes(type)) return h(FileZipOutlined)
  return h(FileOutlined)
}

const loading = ref(false)
const fileList = ref<FileInfo[]>([])
const searchText = ref('')
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const columns = [
  { title: '文件名', key: 'name', dataIndex: 'name' },
  { title: '大小', key: 'size', width: 120 },
  { title: '类型', dataIndex: 'file_type', width: 100 },
  { title: '上传者', dataIndex: 'uploaded_by_name', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '下载次数', dataIndex: 'download_count', width: 100, align: 'center' },
  { title: '权限', key: 'is_public', width: 100 },
  { title: '上传时间', dataIndex: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 250, fixed: 'right' },
]

// 上传相关
const uploadVisible = ref(false)
const uploading = ref(false)
const uploadFileList = ref<any[]>([])
const uploadForm = reactive({
  description: '',
  is_public: false
})

// 预览相关
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewFile = ref<FileInfo | null>(null)
const previewContent = ref('')
const excelData = ref<any[]>([])
const excelColumns = ref<any[]>([])

onMounted(() => {
  fetchFiles()
})

async function fetchFiles() {
  loading.value = true
  try {
    const res = await getFiles({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value
    })
    const data = res.data?.data || res.data
    fileList.value = data.results || []
    pagination.total = data.pagination?.total || data.count || 0
  } catch (error) {
    message.error('获取文件列表失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchFiles()
}

function handleSearch() {
  pagination.current = 1
  fetchFiles()
}

function getStatusColor(status: string) {
  const map: Record<string, string> = {
    active: 'success',
    archived: 'warning',
    deleted: 'error'
  }
  return map[status] || 'default'
}

// ---------------- 上传逻辑 ----------------
function showUploadModal() {
  uploadVisible.value = true
  uploadFileList.value = []
  uploadForm.description = ''
  uploadForm.is_public = false
}

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  uploadFileList.value = [file]
  return false // 阻止自动上传
}

async function handleUpload() {
  if (uploadFileList.value.length === 0) {
    message.warning('请选择要上传的文件')
    return
  }
  
  uploading.value = true
  
  // 获取原始文件对象
  const fileObj = uploadFileList.value[0].originFileObj || uploadFileList.value[0]
  
  const formData = new FormData()
  formData.append('file', fileObj)
  formData.append('name', fileObj.name) // 使用原始文件的名称
  formData.append('description', uploadForm.description)
  formData.append('is_public', uploadForm.is_public ? 'true' : 'false')
  
  try {
    const res = await uploadFile(formData)
    if (res.data.code === 200) {
        message.success('文件上传成功')
        uploadVisible.value = false
        fetchFiles()
    } else {
        message.error(res.data.message || '上传失败')
    }
  } catch (error) {
    message.error('上传失败')
  } finally {
    uploading.value = false
  }
}

// ---------------- 下载逻辑 ----------------
async function handleDownload(record: FileInfo) {
  try {
    message.loading({ content: '正在准备下载...', key: 'download' })
    const response = await downloadFile(record.id)
    
    // 创建 Blob 对象
    const blob = new Blob([response.data], { 
      type: response.headers['content-type'] 
    })
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = record.original_name || record.name
    link.click()
    
    // 释放资源
    window.URL.revokeObjectURL(link.href)
    message.success({ content: '下载开始', key: 'download' })
    
    // 刷新列表更新下载次数
    // fetchFiles() 
  } catch (error) {
    message.error({ content: '下载失败', key: 'download' })
  }
}

// ---------------- 删除逻辑 ----------------
async function handleDelete(record: FileInfo) {
  try {
    await deleteFile(record.id)
    message.success('删除成功')
    fetchFiles()
  } catch (error) {
    message.error('删除失败')
  }
}

// ---------------- 预览逻辑 ----------------
// 文件类型判断
function isImageFile(fileType: string) {
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp']
  return imageTypes.includes(fileType?.toLowerCase())
}

function isPdfFile(fileType: string) {
  return fileType?.toLowerCase() === 'pdf'
}

function isTextFile(fileType: string) {
  const textTypes = ['txt', 'json', 'xml', 'html', 'css', 'js', 'ts', 'vue', 'md', 'log', 'csv']
  return textTypes.includes(fileType?.toLowerCase())
}

function isExcelFile(fileType: string) {
  const excelTypes = ['xlsx', 'xls', 'csv']
  return excelTypes.includes(fileType?.toLowerCase())
}

// 获取文件完整URL
function getFileUrl(fileUrl: string) {
  if (fileUrl.startsWith('http')) {
    return fileUrl
  }
  // 使用环境配置的 API 地址
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  return baseUrl ? `${baseUrl}${fileUrl}` : fileUrl
}

// 预览处理
async function handlePreview(record: FileInfo) {
  previewFile.value = record
  previewVisible.value = true
  previewContent.value = ''
  excelData.value = []
  excelColumns.value = []

  // 文本文件：加载内容
  if (isTextFile(record.file_type)) {
    previewLoading.value = true
    try {
      const response = await apiClient.get(record.file, {
        responseType: 'text',
        baseURL: import.meta.env.VITE_API_BASE_URL || undefined
      })
      previewContent.value = response.data
    } catch (error) {
      message.error('加载文本文件失败')
      previewContent.value = '加载失败'
    } finally {
      previewLoading.value = false
    }
  }
  
  
  // Excel/CSV 文件：解析数据
  else if (isExcelFile(record.file_type)) {
    previewLoading.value = true
    try {
      const response = await downloadFile(record.id)
      const blob = new Blob([response.data])
      
      // 使用 FileReader 读取
      const reader = new FileReader()
      reader.onload = async (e) => {
        try {
          const data = e.target?.result
          
          if (record.file_type === 'csv') {
            // CSV 解析
            const text = new TextDecoder().decode(data as ArrayBuffer)
            const lines = text.split('\n').filter(line => line.trim())
            
            if (lines.length > 0) {
              // 第一行作为表头
              // 第一行作为表头
              const headers = (lines[0] || '').split(',').map((h, i) => ({
                title: h.trim() || `列${i + 1}`,
                dataIndex: `col${i}`,
                key: `col${i}`,
              }))
              excelColumns.value = headers
              
              // 其余行作为数据
              excelData.value = lines.slice(1).map((line, rowIndex) => {
                const values = line.split(',')
                const row: any = { key: rowIndex }
                values.forEach((val, colIndex) => {
                  row[`col${colIndex}`] = val.trim()
                })
                return row
              })
            }
          } else {
            // XLSX/XLS 使用 xlsx 库解析
            const workbook = XLSX.read(data, { type: 'array' })
            
            // 读取第一个工作表
            const firstSheetName = workbook.SheetNames[0]
            if (!firstSheetName) {
                throw new Error('Excel 文件中没有工作表')
            }
            const worksheet = workbook.Sheets[firstSheetName]
            if (!worksheet) {
                throw new Error('无法读取工作表内容')
            }
            
            // 转换为 JSON
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 }) as any[][]
            
            if (jsonData.length > 0) {
              // 第一行作为表头
              const headers = (jsonData[0] as any[]).map((h, i) => ({
                title: h?.toString() || `列${i + 1}`,
                dataIndex: `col${i}`,
                key: `col${i}`,
                width: 150,
              }))
              excelColumns.value = headers
              
              // 其余行作为数据
              excelData.value = jsonData.slice(1).map((row: any[], rowIndex) => {
                const rowData: any = { key: rowIndex }
                row.forEach((val, colIndex) => {
                  rowData[`col${colIndex}`] = val !== null && val !== undefined ? val.toString() : ''
                })
                return rowData
              })
            }
          }
        } catch (err) {
          console.error('解析文件失败:', err)
          message.error('解析文件失败')
        } finally {
          previewLoading.value = false
        }
      }
      reader.readAsArrayBuffer(blob)
    } catch (error) {
      message.error('加载 Excel 文件失败')
      previewLoading.value = false
    }
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

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-text pre {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}
</style>
