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
    
    def __str__(self):
        return self.name


class MappingField(models.Model):
    """字段映射详情"""
    
    class FieldType(models.TextChoices):
        DIRECT = 'direct', '直接映射'  # 源→目标（不需要对照表）
        LOOKUP = 'lookup', '对照表转换'  # 源值→对照表→目标编码
        COMPUTED = 'computed', '计算字段'  # 基于其他字段计算
        DEFAULT = 'default', '默认值'  # 固定默认值
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
    compute_expression = models.CharField(max_length=500, blank=True, verbose_name='计算表达式')
    
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
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    @property
    def progress(self):
        """计算进度百分比"""
        if self.total_rows == 0:
            return 0
        return round(self.processed_rows / self.total_rows * 100, 2)
