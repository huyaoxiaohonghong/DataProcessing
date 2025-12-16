from django.db import models
from django.conf import settings

class LoginLog(models.Model):
    """登录日志"""
    STATUS_CHOICES = (
        (True, '成功'),
        (False, '失败'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='用户')
    username = models.CharField(max_length=150, verbose_name='登录用户名', db_index=True)
    ip = models.GenericIPAddressField(verbose_name='IP地址', null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=500, verbose_name='User Agent', null=True, blank=True)
    status = models.BooleanField(choices=STATUS_CHOICES, default=True, verbose_name='登录状态')
    message = models.CharField(max_length=255, verbose_name='提示信息', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='登录时间', db_index=True)

    class Meta:
        db_table = 'sys_login_log'
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} - {self.created_at}"

class OperationLog(models.Model):
    """操作日志"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    module = models.CharField(max_length=50, verbose_name='模块', null=True, blank=True, db_index=True)
    action = models.CharField(max_length=50, verbose_name='动作', null=True, blank=True)
    method = models.CharField(max_length=10, verbose_name='请求方法', null=True, blank=True)
    path = models.CharField(max_length=255, verbose_name='请求路径', null=True, blank=True)
    params = models.TextField(verbose_name='请求参数', null=True, blank=True)
    ip = models.GenericIPAddressField(verbose_name='IP地址', null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=500, verbose_name='User Agent', null=True, blank=True)
    response_code = models.IntegerField(verbose_name='响应状态码', null=True, blank=True)
    response_time = models.IntegerField(verbose_name='响应时间(ms)', default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间', db_index=True)

    class Meta:
        db_table = 'sys_operation_log'
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"


class Department(models.Model):
    """部门管理"""
    name = models.CharField(max_length=100, verbose_name='部门名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                               related_name='children', verbose_name='上级部门')
    leader = models.CharField(max_length=50, null=True, blank=True, verbose_name='负责人')
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name='联系电话')
    email = models.EmailField(null=True, blank=True, verbose_name='邮箱')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_department'
        verbose_name = '部门'
        verbose_name_plural = '部门管理'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class Menu(models.Model):
    """菜单管理"""
    
    class MenuType(models.TextChoices):
        """菜单类型"""
        DIRECTORY = 'directory', '目录'
        MENU = 'menu', '菜单'
        BUTTON = 'button', '按钮'
    
    name = models.CharField(max_length=50, verbose_name='菜单名称')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name='上级菜单')
    path = models.CharField(max_length=200, null=True, blank=True, verbose_name='路由路径')
    component = models.CharField(max_length=200, null=True, blank=True, verbose_name='组件路径')
    icon = models.CharField(max_length=50, null=True, blank=True, verbose_name='图标')
    menu_type = models.CharField(max_length=20, choices=MenuType.choices, default=MenuType.MENU, verbose_name='菜单类型')
    permission = models.CharField(max_length=100, null=True, blank=True, verbose_name='权限标识')
    sort = models.IntegerField(default=0, verbose_name='排序')
    status = models.BooleanField(default=True, verbose_name='状态')
    visible = models.BooleanField(default=True, verbose_name='是否显示')
    cache = models.BooleanField(default=True, verbose_name='是否缓存')
    remark = models.CharField(max_length=500, null=True, blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'sys_menu'
        verbose_name = '菜单'
        verbose_name_plural = '菜单管理'
        ordering = ['sort', 'id']

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """角色权限关联"""
    
    class DataScope(models.TextChoices):
        """数据权限范围"""
        ALL = 'all', '全部数据'
        DEPT = 'dept', '本部门数据'
        DEPT_AND_CHILD = 'dept_child', '本部门及以下数据'
        SELF = 'self', '仅本人数据'
        CUSTOM = 'custom', '自定义数据'
    
    role = models.CharField(max_length=20, verbose_name='角色')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='role_permissions', verbose_name='菜单')
    data_scope = models.CharField(max_length=20, choices=DataScope.choices, default=DataScope.SELF, verbose_name='数据权限')
    departments = models.ManyToManyField(Department, blank=True, verbose_name='自定义部门')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'sys_role_permission'
        verbose_name = '角色权限'
        verbose_name_plural = '角色权限管理'
        unique_together = ['role', 'menu']

    def __str__(self):
        return f"{self.role} - {self.menu.name}"

