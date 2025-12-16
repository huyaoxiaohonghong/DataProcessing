import time
import json
from .models import OperationLog

class OperationLogMiddleware:
    """操作日志中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 开始计时
        start_time = time.time()
        
        # 处理请求
        response = self.get_response(request)
        
        # 仅记录修改操作，且排除登录接口（避免记录密码）
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and \
           not request.path.endswith('/login/') and \
           request.user.is_authenticated:
            
            # 计算耗时
            duration = int((time.time() - start_time) * 1000)
            
            # 获取请求参数
            try:
                if request.method == 'GET':
                    params = json.dumps(request.GET.dict())
                else:
                    # 尝试解析 JSON body
                    if request.content_type == 'application/json':
                        params = request.body.decode('utf-8')
                    else:
                        params = json.dumps(request.POST.dict())
            except:
                params = '无法解析参数'
                
            # 记录日志
            OperationLog.objects.create(
                user=request.user,
                module=self._get_module(request.path),
                action=self._get_action(request.method),
                method=request.method,
                path=request.path,
                params=params[:2000],  # 截断过长参数
                ip=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                response_code=response.status_code,
                response_time=duration
            )
            
        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_module(self, path):
        if '/users/' in path:
            return '用户管理'
        elif '/files/' in path:
            return '文件管理'
        return '系统'

    def _get_action(self, method):
        actions = {
            'POST': '新增',
            'PUT': '修改',
            'PATCH': '修改',
            'DELETE': '删除'
        }
        return actions.get(method, '读取')
