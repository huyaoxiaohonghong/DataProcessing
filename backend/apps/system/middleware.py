"""
操作日志中间件
Middleware for automatic operation logging
"""
import time
import json
import logging

from .models import OperationLog

logger = logging.getLogger(__name__)

# 慢查询告警阈值（毫秒）
SLOW_QUERY_THRESHOLD_MS = 3000

# 不记录日志的路径列表
EXCLUDED_PATHS = frozenset([
    '/login/',
    '/token/refresh/',
    '/captcha/',
])

# 路径 → 模块映射
MODULE_MAPPING = [
    ('/users/', '用户管理'),
    ('/files/', '文件管理'),
    ('/system/', '系统管理'),
    ('/processing/', '数据处理'),
]

# 不记录参数的路径（敏感接口）
SENSITIVE_PATHS = frozenset([
    '/change-password/',
    '/register/',
])


class OperationLogMiddleware:
    """操作日志中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()
        response = self.get_response(request)
        response_time = int((time.monotonic() - start_time) * 1000)

        # 记录写操作到数据库
        if (
            request.method in ('POST', 'PUT', 'PATCH', 'DELETE')
            and request.user.is_authenticated
            and not self._is_excluded(request.path)
        ):
            params = self._get_params(request) if not self._is_sensitive(request.path) else '[已脱敏]'

            try:
                OperationLog.objects.create(
                    user=request.user,
                    module=self._get_module(request.path),
                    action=self._get_action(request.method),
                    method=request.method,
                    path=request.path[:255],
                    params=params[:2000],
                    ip=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    response_code=response.status_code,
                    response_time=response_time,
                )
            except Exception:
                logger.exception("Failed to save operation log")

        # GET 请求慢查询告警
        if request.method == 'GET' and response_time > SLOW_QUERY_THRESHOLD_MS:
            logger.warning("慢查询告警", extra={
                'path': request.path,
                'method': request.method,
                'duration_ms': response_time,
                'user_id': request.user.id if request.user.is_authenticated else None,
            })

        return response

    @staticmethod
    def _is_excluded(path: str) -> bool:
        return any(path.endswith(excluded) for excluded in EXCLUDED_PATHS)

    @staticmethod
    def _is_sensitive(path: str) -> bool:
        return any(s in path for s in SENSITIVE_PATHS)

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    @staticmethod
    def _get_module(path: str) -> str:
        for pattern, module_name in MODULE_MAPPING:
            if pattern in path:
                return module_name
        return '其他'

    @staticmethod
    def _get_action(method: str) -> str:
        actions = {
            'POST': '新增',
            'PUT': '修改',
            'PATCH': '修改',
            'DELETE': '删除',
        }
        return actions.get(method, '操作')

    @staticmethod
    def _get_params(request) -> str:
        try:
            if request.content_type and 'json' in request.content_type:
                return request.body.decode('utf-8')
            elif request.method == 'GET':
                return json.dumps(request.GET.dict(), ensure_ascii=False)
            else:
                return json.dumps(request.POST.dict(), ensure_ascii=False)
        except Exception:
            return '无法解析参数'
