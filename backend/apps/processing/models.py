"""
数据处理模型
Models for data processing, mapping and tasks
"""
from django.db import models
from django.conf import settings


class DataMapping(models.Model):
    """数据映射配置"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        ACTIVE = 'active', '已激活'
        DISABLED = 'disabled', '已禁用'
    
    name = models.CharField(max_length=200, verbose_name='配置名称')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    
    # 源文件
    source_file = models.ForeignKey(
        'files.File',
        on_delete=models.SET_NULL,
        null=True,
        related_name='source_mappings',
        verbose_name='源文件'
    )
    source_sheet = models.CharField(max_length=100, blank=True, verbose_name='源文件Sheet')
    
    # 对照文件（可选）
    reference_file = models.ForeignKey(
        'files.File',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reference_mappings',
        verbose_name='对照文件'
    )
    reference_sheet = models.CharField(max_length=100, blank=True, verbose_name='对照文件Sheet')
    
    # 目标文件模板（可选）
    target_template = models.ForeignKey(
        'files.File',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_mappings',
        verbose_name='目标文件模板'
    )
    target_sheet = models.CharField(max_length=100, blank=True, verbose_name='目标文件Sheet')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='状态'
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_mappings',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'data_mappings'
        verbose_name = '数据映射配置'
        verbose_name_plural = '数据映射配置'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_by']),
        ]
    
    def __str__(self):
        return self.name


class MappingTargetSheet(models.Model):
    """目标 Sheet 配置（多 sheet 支持）

    一个 DataMapping 下可有多个目标 sheet，每个 sheet 独立持有字段映射集合，
    可通过 SheetLineage 形成 sheet 之间的血缘 DAG。
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', '草稿'
        READY = 'ready', '已就绪'
        DISABLED = 'disabled', '已禁用'

    mapping = models.ForeignKey(
        DataMapping,
        on_delete=models.CASCADE,
        related_name='target_sheets',
        verbose_name='所属配置'
    )
    sheet_name = models.CharField(max_length=100, verbose_name='目标Sheet名称')
    display_name = models.CharField(max_length=200, blank=True, verbose_name='展示名称')
    description = models.TextField(blank=True, default='', verbose_name='说明')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='状态'
    )

    # 每个目标 sheet 可选择性指定源 sheet（留空则继承 DataMapping.source_sheet）
    source_sheet = models.CharField(max_length=100, blank=True, default='', verbose_name='源Sheet')

    sort_order = models.IntegerField(default=0, verbose_name='排序')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'mapping_target_sheets'
        verbose_name = '目标Sheet配置'
        verbose_name_plural = '目标Sheet配置'
        ordering = ['sort_order', 'id']
        unique_together = [('mapping', 'sheet_name')]

    def __str__(self):
        return f"{self.mapping_id}:{self.sheet_name}"


class MappingField(models.Model):
    """字段映射详情"""
    
    class FieldType(models.TextChoices):
        DIRECT = 'direct', '直接映射'  # 源→目标（不需要对照表）
        LOOKUP = 'lookup', '对照表转换'  # 源值→对照表→目标编码
        COMPUTED = 'computed', '计算字段'  # 基于其他字段计算
        DEFAULT = 'default', '默认值'  # 固定默认值
        CROSS_SHEET_REF = 'cross_sheet_ref', '跨Sheet引用'  # 引用另一个目标 sheet 的字段
        # 保留旧类型兼容
        SOURCE_TO_TARGET = 'source_to_target', '源→目标'
        SOURCE_TO_REF = 'source_to_ref', '源→对照'
        REF_TO_TARGET = 'ref_to_target', '对照→目标'
        SOURCE_REF_TARGET = 'source_ref_target', '源→对照→目标'
    
    mapping = models.ForeignKey(
        DataMapping,
        on_delete=models.CASCADE,
        related_name='fields',
        verbose_name='所属配置'
    )

    # 所属目标 Sheet（null 时归属到 DataMapping.target_sheet 兼容旧数据）
    target_sheet_config = models.ForeignKey(
        MappingTargetSheet,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='fields',
        verbose_name='所属目标Sheet'
    )

    # 源字段
    source_field = models.CharField(max_length=200, blank=True, verbose_name='源字段')
    source_field_index = models.IntegerField(default=-1, verbose_name='源字段索引')
    
    # 对照表配置（适用于lookup类型）
    reference_sheet = models.CharField(max_length=100, blank=True, verbose_name='对照表Sheet')
    reference_name_column = models.CharField(max_length=200, blank=True, verbose_name='对照表名称列')
    reference_code_column = models.CharField(max_length=200, blank=True, verbose_name='对照表编码列')
    # 保留旧字段兼容
    reference_field = models.CharField(max_length=200, blank=True, verbose_name='对照字段')
    reference_field_index = models.IntegerField(default=-1, verbose_name='对照字段索引')
    
    # 目标字段
    target_field = models.CharField(max_length=200, verbose_name='目标字段')
    target_field_index = models.IntegerField(default=-1, verbose_name='目标字段索引')
    
    # 映射类型
    field_type = models.CharField(
        max_length=30,
        choices=FieldType.choices,
        default=FieldType.DIRECT,
        verbose_name='映射类型'
    )
    
    # 默认值（适用于default类型）
    default_value = models.CharField(max_length=500, blank=True, verbose_name='默认值')
    
    # 计算表达式（适用于computed类型，如 "{原值}" 或 "{使用月限}/12"）
    # 支持跨 sheet 引用语法：{sheet.字段} 或 AGG:SUM({sheetA.字段})
    compute_expression = models.CharField(max_length=500, blank=True, verbose_name='计算表达式')

    # 跨 Sheet 引用配置（field_type=cross_sheet_ref 时使用）
    source_target_sheet = models.ForeignKey(
        MappingTargetSheet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referenced_by_fields',
        verbose_name='引用的目标Sheet'
    )
    source_target_field = models.CharField(max_length=200, blank=True, default='', verbose_name='引用的目标Sheet字段')
    # 跨 sheet 聚合类型: none / sum / count / avg / min / max / first
    aggregation = models.CharField(max_length=20, blank=True, default='', verbose_name='聚合方式')
    
    # 数据转换规则（JSON格式，可选）
    transform_rule = models.JSONField(blank=True, null=True, verbose_name='转换规则')
    
    # 排序
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    
    class Meta:
        db_table = 'mapping_fields'
        verbose_name = '字段映射'
        verbose_name_plural = '字段映射'
        ordering = ['sort_order']
    
    def __str__(self):
        if self.source_field:
            return f"{self.source_field} → {self.target_field}"
        return f"→ {self.target_field}"


class SheetLineage(models.Model):
    """Sheet 级血缘：描述一个目标 sheet 依赖另一个目标 sheet 的关系。

    执行任务时，处理顺序按 SheetLineage 构成的 DAG 进行拓扑排序。
    """

    class RelationType(models.TextChoices):
        DERIVED = 'derived', '派生'          # 下游由上游派生
        AGGREGATED = 'aggregated', '聚合'    # 下游是上游的聚合
        JOINED = 'joined', '关联'            # 下游与上游按键关联
        REFERENCE = 'reference', '引用'      # 下游引用上游某些字段

    mapping = models.ForeignKey(
        DataMapping,
        on_delete=models.CASCADE,
        related_name='sheet_lineages',
        verbose_name='所属配置'
    )
    upstream = models.ForeignKey(
        MappingTargetSheet,
        on_delete=models.CASCADE,
        related_name='downstream_lineages',
        verbose_name='上游Sheet'
    )
    downstream = models.ForeignKey(
        MappingTargetSheet,
        on_delete=models.CASCADE,
        related_name='upstream_lineages',
        verbose_name='下游Sheet'
    )
    relation_type = models.CharField(
        max_length=20,
        choices=RelationType.choices,
        default=RelationType.DERIVED,
        verbose_name='关系类型'
    )
    # join_keys 示例: [{"upstream": "部门编号", "downstream": "部门编号"}]
    join_keys = models.JSONField(blank=True, null=True, verbose_name='关联键配置')
    description = models.CharField(max_length=500, blank=True, default='', verbose_name='关系描述')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sheet_lineages'
        verbose_name = 'Sheet血缘'
        verbose_name_plural = 'Sheet血缘'
        # Req 3.5: 同一 mapping 下禁止 (upstream, downstream, relation_type) 三元组重复。
        # 显式包含 mapping 作为 DB 兜底，即便 upstream/downstream 已隐含 mapping。
        unique_together = [('mapping', 'upstream', 'downstream', 'relation_type')]
        ordering = ['id']

    def __str__(self):
        return f"{self.upstream_id} → {self.downstream_id} ({self.relation_type})"


class FieldLineage(models.Model):
    """字段级血缘：描述下游字段的计算依赖哪些上游字段。

    用于可视化字段之间的数据流转，即使下游字段的计算由 compute_expression 表达，
    也通过该表记录显式血缘以支撑影响分析。
    """

    mapping = models.ForeignKey(
        DataMapping,
        on_delete=models.CASCADE,
        related_name='field_lineages',
        verbose_name='所属配置'
    )
    upstream_sheet = models.ForeignKey(
        MappingTargetSheet,
        on_delete=models.CASCADE,
        related_name='downstream_field_lineages',
        verbose_name='上游Sheet'
    )
    upstream_field = models.CharField(max_length=200, verbose_name='上游字段')

    downstream_sheet = models.ForeignKey(
        MappingTargetSheet,
        on_delete=models.CASCADE,
        related_name='upstream_field_lineages',
        verbose_name='下游Sheet'
    )
    downstream_field = models.CharField(max_length=200, verbose_name='下游字段')

    # 传播方式: direct / computed / aggregated / lookup
    transform = models.CharField(max_length=30, default='direct', verbose_name='传播方式')
    note = models.CharField(max_length=500, blank=True, default='', verbose_name='备注')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'field_lineages'
        verbose_name = '字段血缘'
        verbose_name_plural = '字段血缘'
        ordering = ['id']
        indexes = [
            models.Index(fields=['mapping', 'downstream_sheet'], name='field_linea_mapping_down_idx'),
            models.Index(fields=['mapping', 'upstream_sheet'], name='field_linea_mapping_up_idx'),
        ]

    def __str__(self):
        return f"{self.upstream_sheet_id}.{self.upstream_field} → {self.downstream_sheet_id}.{self.downstream_field}"


class ProcessingTask(models.Model):
    """数据处理任务"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', '待执行'
        RUNNING = 'running', '执行中'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'
        CANCELLED = 'cancelled', '已取消'
    
    name = models.CharField(max_length=200, verbose_name='任务名称')
    
    # 关联配置
    mapping = models.ForeignKey(
        DataMapping,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='映射配置'
    )
    
    # 任务状态
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='状态'
    )
    
    # 执行信息
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    # 处理统计
    total_rows = models.IntegerField(default=0, verbose_name='总行数')
    processed_rows = models.IntegerField(default=0, verbose_name='已处理行数')
    success_rows = models.IntegerField(default=0, verbose_name='成功行数')
    error_rows = models.IntegerField(default=0, verbose_name='错误行数')
    
    # 结果文件
    result_file = models.FileField(
        upload_to='processing_results/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='结果文件'
    )
    
    # 错误信息
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    # Celery 任务 ID
    celery_task_id = models.CharField(max_length=255, blank=True, default='', verbose_name='Celery任务ID')
    
    # 创建信息
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processing_tasks',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'processing_tasks'
        verbose_name = '处理任务'
        verbose_name_plural = '处理任务'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_by']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def progress(self):
        """计算进度百分比"""
        if self.total_rows == 0:
            return 0
        return round(self.processed_rows / self.total_rows * 100, 2)


class TaskSheetResult(models.Model):
    """任务中每个目标 Sheet 的执行结果（生命周期记录）"""

    class Status(models.TextChoices):
        PENDING = 'pending', '待执行'
        RUNNING = 'running', '执行中'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '失败'
        SKIPPED = 'skipped', '已跳过'

    task = models.ForeignKey(
        ProcessingTask,
        on_delete=models.CASCADE,
        related_name='sheet_results',
        verbose_name='所属任务'
    )
    target_sheet = models.ForeignKey(
        MappingTargetSheet,
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_results',
        verbose_name='目标Sheet配置'
    )
    sheet_name = models.CharField(max_length=100, verbose_name='Sheet名称')

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='状态'
    )

    total_rows = models.IntegerField(default=0, verbose_name='总行数')
    success_rows = models.IntegerField(default=0, verbose_name='成功行数')
    error_rows = models.IntegerField(default=0, verbose_name='错误行数')

    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    duration_ms = models.IntegerField(default=0, verbose_name='耗时(毫秒)')

    error_message = models.TextField(blank=True, default='', verbose_name='错误信息')

    # 执行顺序（拓扑排序后的序号，0 起始）
    execution_order = models.IntegerField(default=0, verbose_name='执行顺序')

    class Meta:
        db_table = 'task_sheet_results'
        verbose_name = '任务Sheet结果'
        verbose_name_plural = '任务Sheet结果'
        ordering = ['task', 'execution_order']
        indexes = [
            models.Index(fields=['task', 'status'], name='task_sheet_res_task_st_idx'),
        ]

    def __str__(self):
        return f"Task#{self.task_id} - {self.sheet_name} ({self.get_status_display()})"
