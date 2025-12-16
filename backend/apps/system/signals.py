from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from .models import LoginLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """记录登录成功"""
    LoginLog.objects.create(
        user=user,
        username=user.username,
        ip=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        status=True,
        message='登录成功'
    )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """记录登录失败"""
    username = credentials.get('username', 'unknown')
    LoginLog.objects.create(
        username=username,
        ip=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        status=False,
        message='用户名或密码错误'
    )
