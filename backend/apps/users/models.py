"""
用户模型定义
Custom User Model with extended fields for the Data Processing System
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    自定义用户模型
    扩展 Django 默认用户模型，添加额外字段
    """
    
    class Role(models.TextChoices):
        """用户角色"""
        SUPER_ADMIN = 'super_admin', '超级管理员'
        ADMIN = 'admin', '管理员'
        USER = 'user', '普通用户'
    
    # 扩展字段
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name='手机号'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='角色'
    )
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name='创建者'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='头像'
    )
    department = models.ForeignKey(
        'system.Department',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users',
        verbose_name='部门'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否激活'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

