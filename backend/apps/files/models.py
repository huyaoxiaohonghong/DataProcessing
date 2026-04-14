"""
文件模型定义
File Model for the Data Processing System
"""
from django.db import models
from django.conf import settings
import os
import uuid


def file_upload_path(instance, filename):
    """生成文件上传路径"""
    ext = filename.split('.')[-1] if '.' in filename else ''
    new_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return os.path.join('uploads', instance.created_at.strftime('%Y/%m'), new_filename)


class FileCategory(models.Model):
    """文件分类"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='父分类'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'file_categories'
        verbose_name = '文件分类'
        verbose_name_plural = '文件分类'
        ordering = ['name']

    def __str__(self):
        return self.name


class File(models.Model):
    """文件模型"""
    
    class Status(models.TextChoices):
        """文件状态"""
        ACTIVE = 'active', '正常'
        ARCHIVED = 'archived', '已归档'
        DELETED = 'deleted', '已删除'
    
    # 基本信息
    name = models.CharField(max_length=255, verbose_name='文件名')
    original_name = models.CharField(max_length=255, verbose_name='原始文件名')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    
    # 文件信息
    file = models.FileField(upload_to='uploads/%Y/%m/', verbose_name='文件')
    file_size = models.BigIntegerField(default=0, verbose_name='文件大小(字节)')
    file_type = models.CharField(max_length=100, blank=True, verbose_name='文件类型')
    mime_type = models.CharField(max_length=100, blank=True, verbose_name='MIME类型')
    
    # 分类和标签
    category = models.ForeignKey(
        FileCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files',
        verbose_name='分类'
    )
    tags = models.CharField(max_length=500, blank=True, verbose_name='标签(逗号分隔)')
    
    # 状态和权限
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='状态'
    )
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    
    # 上传信息
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
        verbose_name='上传者'
    )
    department = models.ForeignKey(
        'system.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files',
        verbose_name='所属部门'
    )
    download_count = models.IntegerField(default=0, verbose_name='下载次数')
    
    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'files'
        verbose_name = '文件'
        verbose_name_plural = '文件'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'file_type']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 自动获取文件信息
        if self.file:
            if not self.original_name:
                self.original_name = self.file.name
            if not self.file_size and hasattr(self.file, 'size'):
                self.file_size = self.file.size
            if not self.file_type:
                ext = self.file.name.split('.')[-1].lower() if '.' in self.file.name else ''
                self.file_type = ext
        super().save(*args, **kwargs)

    @property
    def file_size_display(self):
        """格式化显示文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
