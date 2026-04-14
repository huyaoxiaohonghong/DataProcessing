import { ref, reactive, type Ref } from 'vue'
import type { AxiosResponse } from 'axios'

/**
 * 表格请求参数（分页部分）
 */
export interface TableFetchParams {
  page: number
  page_size: number
  [key: string]: unknown
}

/**
 * useTable 配置选项
 */
export interface UseTableOptions<T, P extends Record<string, unknown> = Record<string, unknown>> {
  /** 数据获取函数，接收分页 + 额外参数，返回 AxiosResponse */
  fetchApi: (params: TableFetchParams & P) => Promise<AxiosResponse>
  /** 每页条数，默认 10 */
  pageSize?: number
  /** 是否在初始化时自动加载，默认 false（由调用方在 onMounted 中控制） */
  immediate?: boolean
  /** 从响应中提取列表数据，默认兼容两种后端格式 */
  extractData?: (res: AxiosResponse) => T[]
  /** 从响应中提取总条数，默认兼容两种后端格式 */
  extractTotal?: (res: AxiosResponse) => number
}

/**
 * 通用表格分页、加载状态 composable
 *
 * 提取 ant-design-vue a-table 常见的分页、loading、数据获取逻辑，
 * 适配项目中两种后端响应格式：
 *   - ApiResponse 格式: res.data.data.results / res.data.data.pagination.total
 *   - DRF 原始格式:    res.data.results / res.data.count
 */
export function useTable<T = any, P extends Record<string, unknown> = Record<string, unknown>>(
  options: UseTableOptions<T, P>
) {
  const {
    fetchApi,
    pageSize = 10,
    immediate = false,
  } = options

  const loading = ref(false)
  const dataSource: Ref<T[]> = ref([])

  const pagination = reactive({
    current: 1,
    pageSize,
    total: 0,
    showSizeChanger: true,
    showTotal: (total: number) => `共 ${total} 条`,
  })

  /** 默认数据提取：兼容 ApiResponse 和 DRF 两种格式 */
  function defaultExtractData(res: AxiosResponse): T[] {
    const d = res.data?.data || res.data
    return d?.results ?? []
  }

  function defaultExtractTotal(res: AxiosResponse): number {
    const d = res.data?.data || res.data
    return d?.pagination?.total ?? d?.count ?? 0
  }

  const extractData = options.extractData ?? defaultExtractData
  const extractTotal = options.extractTotal ?? defaultExtractTotal

  /**
   * 加载数据
   * @param extraParams 额外的查询参数（搜索、筛选等）
   */
  async function fetchData(extraParams?: P) {
    loading.value = true
    try {
      const params = {
        page: pagination.current,
        page_size: pagination.pageSize,
        ...(extraParams as any),
      } as TableFetchParams & P

      const res = await fetchApi(params)
      dataSource.value = extractData(res) as any
      pagination.total = extractTotal(res)
    } finally {
      loading.value = false
    }
  }

  /**
   * ant-design-vue a-table @change 事件处理
   */
  function handleTableChange(pag: { current?: number; pageSize?: number }) {
    if (pag.current !== undefined) pagination.current = pag.current
    if (pag.pageSize !== undefined) pagination.pageSize = pag.pageSize
    fetchData()
  }

  /**
   * 搜索 / 筛选时调用，重置到第一页并重新加载
   */
  function resetAndFetch(extraParams?: P) {
    pagination.current = 1
    fetchData(extraParams)
  }

  if (immediate) {
    fetchData()
  }

  return {
    loading,
    dataSource,
    pagination,
    fetchData,
    handleTableChange,
    resetAndFetch,
  }
}
