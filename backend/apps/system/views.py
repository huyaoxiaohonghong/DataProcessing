from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from django.contrib.auth import get_user_model
from .models import LoginLog, OperationLog, Department, Menu, RolePermission
from .serializers import (
    LoginLogSerializer, OperationLogSerializer, 
    DepartmentSerializer, DepartmentSimpleSerializer,
    MenuSerializer, MenuSimpleSerializer,
    RolePermissionSerializer
)
from .cache import CacheService, CacheKeys, cache_response

User = get_user_model()

class LoginLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    登录日志视图
    - 超级管理员: 可查看所有日志
    - 管理员: 可查看自己及创建用户的日志
    - 普通用户: 只能查看自己的日志
    """
    queryset = LoginLog.objects.all()
    serializer_class = LoginLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'username']
    search_fields = ['username', 'ip']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据角色过滤日志"""
        user = self.request.user
        if user.role == 'super_admin':
            # 超级管理员可以看到所有日志
            return LoginLog.objects.all()
        elif user.role == 'admin':
            # 管理员可以看到自己及创建用户的日志
            created_user_ids = User.objects.filter(created_by=user).values_list('id', flat=True)
            allowed_user_ids = list(created_user_ids) + [user.id]
            return LoginLog.objects.filter(
                models.Q(user_id__in=allowed_user_ids) | models.Q(username=user.username)
            )
        else:
            # 普通用户只能看到自己的日志
            return LoginLog.objects.filter(
                models.Q(user=user) | models.Q(username=user.username)
            )

class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    操作日志视图
    - 超级管理员: 可查看所有日志
    - 管理员: 可查看自己及创建用户的日志
    - 普通用户: 只能查看自己的日志
    """
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['module', 'action', 'method', 'response_code']
    search_fields = ['user__username', 'path', 'ip']
    ordering_fields = ['created_at', 'response_time']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据角色过滤日志"""
        user = self.request.user
        if user.role == 'super_admin':
            # 超级管理员可以看到所有日志
            return OperationLog.objects.all()
        elif user.role == 'admin':
            # 管理员可以看到自己及创建用户的日志
            created_user_ids = User.objects.filter(created_by=user).values_list('id', flat=True)
            allowed_user_ids = list(created_user_ids) + [user.id]
            return OperationLog.objects.filter(user_id__in=allowed_user_ids)
        else:
            # 普通用户只能看到自己的日志
            return OperationLog.objects.filter(user=user)


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门管理视图"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'parent']
    search_fields = ['name', 'code', 'leader']
    ordering_fields = ['sort', 'created_at']
    ordering = ['sort', 'id']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # 检查是否请求树形结构
        if request.query_params.get('tree') == 'true':
            # 只获取顶级部门
            queryset = queryset.filter(parent__isnull=True)
            serializer = self.get_serializer(queryset, many=True, context={'tree': True})
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': serializer.data
            })
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 清除部门缓存
        CacheService.clear_department_cache()
        return Response({
            'code': 200,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # 清除部门缓存
        CacheService.clear_department_cache()
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 检查是否有子部门
        if instance.children.exists():
            return Response({
                'code': 400,
                'message': '存在子部门，无法删除'
            }, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        # 清除部门缓存
        CacheService.clear_department_cache()
        return Response({
            'code': 200,
            'message': '删除成功'
        })
    
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """获取简单部门列表（用于下拉选择）- 带缓存"""
        # 尝试从缓存获取
        cached_data = CacheService.get(CacheKeys.DEPARTMENT_SIMPLE)
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = self.get_queryset().filter(status=True)
        serializer = DepartmentSimpleSerializer(queryset, many=True)
        response_data = {
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        }
        # 缓存结果
        CacheService.set(CacheKeys.DEPARTMENT_SIMPLE, response_data, CacheService.LONG_TIMEOUT)
        return Response(response_data)


class MenuViewSet(viewsets.ModelViewSet):
    """菜单管理视图"""
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['menu_type', 'status', 'visible']
    search_fields = ['name', 'path', 'permission']
    ordering_fields = ['sort', 'created_at']
    ordering = ['sort', 'id']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # 检查是否请求树形结构
        if request.query_params.get('tree') == 'true':
            queryset = queryset.filter(parent__isnull=True)
            serializer = self.get_serializer(queryset, many=True, context={'tree': True})
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': serializer.data
            })
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 清除菜单缓存
        CacheService.clear_menu_cache()
        return Response({
            'code': 200,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # 清除菜单缓存
        CacheService.clear_menu_cache()
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.children.exists():
            return Response({
                'code': 400,
                'message': '存在子菜单，无法删除'
            }, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        # 清除菜单缓存
        CacheService.clear_menu_cache()
        return Response({
            'code': 200,
            'message': '删除成功'
        })
    
    @action(detail=False, methods=['get'])
    def simple(self, request):
        """获取简单菜单列表（用于下拉选择）- 带缓存"""
        cached_data = CacheService.get(CacheKeys.MENU_SIMPLE)
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = self.get_queryset().filter(status=True)
        serializer = MenuSimpleSerializer(queryset, many=True)
        response_data = {
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        }
        CacheService.set(CacheKeys.MENU_SIMPLE, response_data, CacheService.LONG_TIMEOUT)
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """获取菜单类型选项"""
        types = [{'value': choice[0], 'label': choice[1]} for choice in Menu.MenuType.choices]
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': types
        })


class RolePermissionViewSet(viewsets.ModelViewSet):
    """角色权限视图"""
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['role', 'menu', 'data_scope']
    ordering = ['-created_at']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'code': 200,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return Response({
            'code': 200,
            'message': '删除成功'
        })
    
    @action(detail=False, methods=['get'])
    def scopes(self, request):
        """获取数据权限范围选项"""
        scopes = [{'value': choice[0], 'label': choice[1]} for choice in RolePermission.DataScope.choices]
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': scopes
        })
    
    @action(detail=False, methods=['post'])
    def batch(self, request):
        """批量设置角色权限"""
        role = request.data.get('role')
        menu_ids = request.data.get('menu_ids', [])
        
        if not role:
            return Response({
                'code': 400,
                'message': '角色不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 删除该角色的所有权限
        RolePermission.objects.filter(role=role).delete()
        
        # 批量创建新权限
        for menu_id in menu_ids:
            RolePermission.objects.create(role=role, menu_id=menu_id)
        
        return Response({
            'code': 200,
            'message': '设置成功'
        })


# ============== 滑动验证码 ==============

from rest_framework.views import APIView

class CaptchaView(APIView):
    """
    滑动验证码接口
    GET /api/system/captcha/ - 获取验证码
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """获取滑动验证码"""
        try:
            from apps.system.services.captcha import CaptchaService
            captcha_data = CaptchaService.generate_captcha()
            return Response({
                'code': 200,
                'message': '获取成功',
                'data': captcha_data
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'生成验证码失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

