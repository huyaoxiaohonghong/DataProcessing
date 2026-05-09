/**
 * 数据处理 API
 * Processing APIs for mapping and tasks
 */
import apiClient from './client'

// ============== 数据映射配置 ==============

export interface MappingField {
    id?: number
    // 所属目标 Sheet（多 sheet 模式下由前端填 target_sheet_name 给后端）
    target_sheet_config?: number | null
    target_sheet_name?: string

    source_field: string
    source_field_index: number

    // 对照表配置
    reference_sheet: string
    reference_name_column: string
    reference_code_column: string
    reference_field: string
    reference_field_index: number

    // 目标字段
    target_field: string
    target_field_index: number

    // 映射类型与配置
    field_type: 'direct' | 'lookup' | 'computed' | 'default' | 'cross_sheet_ref' | 'source_to_target' | 'source_to_ref' | 'ref_to_target' | 'source_ref_target'
    field_type_display?: string

    default_value: string
    compute_expression: string

    // 跨 sheet 引用
    source_target_sheet?: number | null
    source_target_sheet_name?: string
    source_target_field?: string
    aggregation?: '' | 'sum' | 'count' | 'avg' | 'min' | 'max' | 'first'

    transform_rule: any
    sort_order: number
}

// 多 sheet 支持：目标 Sheet 配置
export interface MappingTargetSheet {
    id?: number
    sheet_name: string
    display_name?: string
    description?: string
    status?: 'draft' | 'ready' | 'disabled'
    status_display?: string
    source_sheet?: string
    sort_order: number
    fields: MappingField[]
    field_count?: number
    created_at?: string
    updated_at?: string
}

// Sheet 血缘（写入版：用 sheet_name 指向）
export interface SheetLineageEdge {
    id?: number
    upstream: string                  // 上游 sheet_name
    downstream: string                // 下游 sheet_name
    relation_type: 'derived' | 'aggregated' | 'joined' | 'reference'
    relation_type_display?: string
    join_keys?: Array<{ upstream: string; downstream: string }> | null
    description?: string
}

// 字段血缘
export interface FieldLineageEdge {
    id?: number
    upstream_sheet: string            // upstream sheet_name
    upstream_field: string
    downstream_sheet: string          // downstream sheet_name
    downstream_field: string
    transform?: 'direct' | 'computed' | 'aggregated' | 'lookup'
    note?: string
}

export interface DataMapping {
    id: number
    name: string
    description: string | null
    source_file: number | null
    source_file_name: string | null
    source_sheet: string
    reference_file: number | null
    reference_file_name: string | null
    reference_sheet: string
    target_template: number | null
    target_template_name: string | null
    target_sheet: string
    status: 'draft' | 'active' | 'disabled'
    status_display: string
    fields: MappingField[]
    target_sheets?: MappingTargetSheet[]
    sheet_lineages?: Array<SheetLineageEdge & { upstream: number; downstream: number; upstream_name?: string; downstream_name?: string }>
    field_lineages?: Array<FieldLineageEdge & { upstream_sheet: number; downstream_sheet: number; upstream_sheet_name?: string; downstream_sheet_name?: string }>
    task_count: number
    created_by: number | null
    created_by_name: string | null
    created_at: string
    updated_at: string
}

export interface DataMappingCreate {
    name: string
    description?: string
    source_file?: number
    source_sheet?: string
    reference_file?: number
    reference_sheet?: string
    target_template?: number
    target_sheet?: string
    status?: string
    fields?: MappingField[]
    // 多 sheet
    target_sheets?: MappingTargetSheet[]
    sheet_lineages?: SheetLineageEdge[]
    field_lineages?: FieldLineageEdge[]
}

export interface SheetField {
    name: string
    index: number
}

export interface SheetInfo {
    sheet_name: string
    fields: SheetField[]
}

export interface FileFieldsResult {
    file_id: number
    file_name: string
    sheets: SheetInfo[]
}

// 获取配置列表
export const getMappings = (params?: { page?: number; page_size?: number; search?: string; status?: string }) => {
    return apiClient.get<any>('/processing/mappings/', { params })
}

// 获取单个配置
export const getMapping = (id: number) => {
    return apiClient.get<any>(`/processing/mappings/${id}/`)
}

// 创建配置
export const createMapping = (data: DataMappingCreate) => {
    return apiClient.post<any>('/processing/mappings/', data)
}

// 更新配置
export const updateMapping = (id: number, data: Partial<DataMappingCreate>) => {
    return apiClient.put<any>(`/processing/mappings/${id}/`, data)
}

// 删除配置
export const deleteMapping = (id: number) => {
    return apiClient.delete<any>(`/processing/mappings/${id}/`)
}

// 激活配置
export const activateMapping = (id: number) => {
    return apiClient.post<any>(`/processing/mappings/${id}/activate/`)
}

// 禁用配置
export const disableMapping = (id: number) => {
    return apiClient.post<any>(`/processing/mappings/${id}/disable/`)
}

// 解析文件字段
export const parseFileFields = (fileId: number) => {
    return apiClient.post<any>('/processing/mappings/parse_file/', { file_id: fileId })
}

// 获取血缘图
export interface LineageGraph {
    nodes: Array<{
        id: number
        sheet_name: string
        display_name: string
        status: string
        execution_order: number
        fields: Array<{ id: number; name: string; field_type: string; sort_order: number }>
    }>
    edges: Array<{
        id: number
        source: number
        target: number
        relation_type: string
        relation_type_display: string
        description: string
        join_keys: any
    }>
    field_edges: Array<{
        id: number
        source_sheet: number
        source_sheet_name: string
        source_field: string
        target_sheet: number
        target_sheet_name: string
        target_field: string
        transform: string
        note: string
    }>
}

export const getMappingLineage = (id: number) => {
    return apiClient.get<any>(`/processing/mappings/${id}/lineage/`)
}

// ============== 处理任务 ==============

export interface ProcessingTask {
    id: number
    name: string
    mapping: number
    mapping_name: string
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
    status_display: string
    started_at: string | null
    completed_at: string | null
    total_rows: number
    processed_rows: number
    success_rows: number
    error_rows: number
    progress: number
    result_file: string | null
    error_message: string | null
    sheet_results?: TaskSheetResult[]
    created_by: number | null
    created_by_name: string | null
    created_at: string
}

export interface TaskSheetResult {
    id: number
    sheet_name: string
    target_sheet: number | null
    status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
    status_display: string
    total_rows: number
    success_rows: number
    error_rows: number
    progress: number
    started_at: string | null
    completed_at: string | null
    duration_ms: number
    error_message: string
    execution_order: number
}

export interface TaskCreate {
    name: string
    mapping: number
}

// 获取任务列表
export const getTasks = (params?: { page?: number; page_size?: number; search?: string; status?: string; mapping?: number }) => {
    return apiClient.get<any>('/processing/tasks/', { params })
}

// 获取单个任务
export const getTask = (id: number) => {
    return apiClient.get<any>(`/processing/tasks/${id}/`)
}

// 创建任务
export const createTask = (data: TaskCreate) => {
    return apiClient.post<any>('/processing/tasks/', data)
}

// 删除任务
export const deleteTask = (id: number) => {
    return apiClient.delete<any>(`/processing/tasks/${id}/`)
}

// 执行任务
export const executeTask = (id: number) => {
    return apiClient.post<any>(`/processing/tasks/${id}/execute/`)
}

// 取消任务（待执行状态）
export const cancelTask = (id: number) => {
    return apiClient.post<any>(`/processing/tasks/${id}/cancel/`)
}

// 终止任务（运行中状态）
export const terminateTask = (id: number) => {
    return apiClient.post<any>(`/processing/tasks/${id}/terminate/`)
}

// 下载结果文件
export const downloadTaskResult = (id: number) => {
    return apiClient.get(`/processing/tasks/${id}/download/`, {
        responseType: 'blob'
    })
}

// 获取任务 Sheet 执行结果（多 sheet 时使用）
export const getTaskSheetResults = (id: number) => {
    return apiClient.get<any>(`/processing/tasks/${id}/sheet_results/`)
}
