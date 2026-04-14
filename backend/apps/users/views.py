"""
用户视图
Views for user authentication and management
"""
from rest_framework import status, generics, permissions, viewsets, filters
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    UserSerializer, 
    UserCreateSerializer, 
    ChangePasswordSerializer,
    LoginSerializer,
    UserAdminSerializer
)
from apps.system.cache import CacheService
from utils.response import ApiResponse

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    用户注册接口
    POST /api/users/register/
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserCreateSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # 生成 JWT Token
        refresh = RefreshToken.for_user(user)
        
        return ApiResponse.created(data={
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, message='注册成功')


from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.contrib.auth.models import update_last_login

class LoginView(APIView):
    """
    用户登录接口
    POST /api/users/login/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        from apps.system.services.captcha import CaptchaService
        from apps.system.rate_limiter import RateLimiter

        ip = RateLimiter.get_client_ip(request)

        # 1. IP 封锁检查
        if RateLimiter.is_ip_blocked(ip):
            return ApiResponse.error(message='您的 IP 已被临时封锁，请 30 分钟后再试', code=429, http_status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 2. 登录频率限制检查：每分钟 5 次
        if RateLimiter.is_rate_limited(f"rate:login:{ip}", 5, 60):
            return ApiResponse.error(message='登录尝试过于频繁，请 1 分钟后再试', code=429, http_status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 3. 验证滑动验证码
        captcha_key = request.data.get('captcha_key')
        x_offset = request.data.get('x_offset')
        
        if not captcha_key or x_offset is None:
            return ApiResponse.error(message='请完成滑动验证')
        
        # 获取增强验证参数
        trajectory = request.data.get('trajectory')
        duration = request.data.get('duration')
        fingerprint = request.data.get('fingerprint')

        # 验证滑动位置（增强版：含 IP、指纹、轨迹、耗时）
        success, message = CaptchaService.verify_captcha(
            captcha_key, int(x_offset),
            ip=ip,
            fingerprint=fingerprint,
            trajectory=trajectory,
            duration=int(duration) if duration is not None else None,
        )
        if not success:
            return ApiResponse.error(message=message)
        
        # 4. 验证用户名密码
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        
        if user is None:
            # 记录登录失败
            RateLimiter.record_login_failure(ip)
            # 发送登录失败信号
            user_login_failed.send(
                sender=__name__, 
                credentials={'username': serializer.validated_data['username']}, 
                request=request
            )
            return ApiResponse.unauthorized(message='用户名或密码错误')
        
        if not user.is_active:
            # 记录登录失败
            RateLimiter.record_login_failure(ip)
            # 发送登录失败信号
            user_login_failed.send(
                sender=__name__, 
                credentials={'username': serializer.validated_data['username']}, 
                request=request
            )
            return ApiResponse.forbidden(message='账户已被禁用')
        
        # 发送登录成功信号
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        # 更新最后登录时间
        update_last_login(None, user)
        
        # 生成 JWT Token
        refresh = RefreshToken.for_user(user)
        
        return ApiResponse.success(data={
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, message='登录成功')


class LogoutView(APIView):
    """
    用户登出接口
    POST /api/users/logout/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return ApiResponse.success(message='登出成功')
        except Exception:
            return ApiResponse.success(message='登出成功')


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    用户个人信息接口
    GET/PUT /api/users/profile/
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ApiResponse.success(data=serializer.data, message='获取成功')
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return ApiResponse.success(data=serializer.data, message='更新成功')


class ChangePasswordView(APIView):
    """
    修改密码接口
    POST /api/users/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return ApiResponse.error(message='原密码错误')
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return ApiResponse.success(message='密码修改成功')


class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理接口
    - 超级管理员: 可管理所有用户，可设置任何角色
    - 管理员: 可管理用户，但只能设置角色为普通用户
    - 普通用户: 无权限
    """
    queryset = User.objects.select_related('department', 'created_by').all()
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['created_at', 'username']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据角色过滤用户列表"""
        user = self.request.user
        if user.role == 'super_admin':
            # 超级管理员可以看到所有用户
            return User.objects.all()
        elif user.role == 'admin':
            # 管理员可以看到自己创建的用户和自己
            return User.objects.filter(
                models.Q(created_by=user) | models.Q(id=user.id)
            )
        else:
            # 普通用户只能看到自己
            return User.objects.filter(id=user.id)
    
    def check_permissions(self, request):
        """检查操作权限"""
        super().check_permissions(request)
        # 只有管理员及以上可以访问用户管理
        if request.user.role not in ['super_admin', 'admin']:
            self.permission_denied(request, message='您没有权限访问用户管理')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(data=serializer.data, message='获取成功')
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 清除用户缓存
        CacheService.clear_user_cache()
        return ApiResponse.created(data=serializer.data, message='创建成功')
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 管理员不能修改超级管理员或其他管理员
        if request.user.role == 'admin' and instance.role in ['super_admin', 'admin']:
            return ApiResponse.forbidden(message='您没有权限修改该用户')
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # 清除用户缓存
        CacheService.clear_user_cache(instance.id)
        return ApiResponse.success(data=serializer.data, message='更新成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 不能删除自己
        if instance.id == request.user.id:
            return ApiResponse.error(message='不能删除当前登录用户')
        
        # 管理员不能删除超级管理员或其他管理员
        if request.user.role == 'admin' and instance.role in ['super_admin', 'admin']:
            return ApiResponse.forbidden(message='您没有权限删除该用户')
        
        self.perform_destroy(instance)
        # 清除用户缓存
        CacheService.clear_user_cache(instance.id)
        return ApiResponse.success(message='删除成功')
    
    @action(detail=False, methods=['get'])
    def roles(self, request):
        """获取角色选项（根据当前用户权限返回可选角色）"""
        user = request.user
        if user.role == 'super_admin':
            # 超级管理员可以设置所有角色
            roles = [{'value': choice[0], 'label': choice[1]} for choice in User.Role.choices]
        elif user.role == 'admin':
            # 管理员只能设置普通用户
            roles = [{'value': 'user', 'label': '普通用户'}]
        else:
            roles = []
        return ApiResponse.success(data=roles, message='获取成功')

