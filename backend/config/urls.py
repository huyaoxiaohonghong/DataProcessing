"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def healthz(_request):
    """健康检查端点（免认证，供容器 healthcheck / 反代探针使用）"""
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', healthz),
    # API 路由
    path('api/users/', include('apps.users.urls', namespace='users')),
    path('api/files/', include('apps.files.urls', namespace='files')),
    path('api/system/', include('apps.system.urls', namespace='system')),
    path('api/processing/', include('apps.processing.urls', namespace='processing')),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
