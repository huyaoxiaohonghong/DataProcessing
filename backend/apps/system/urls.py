from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoginLogViewSet, OperationLogViewSet, DepartmentViewSet,
    MenuViewSet, RolePermissionViewSet, CaptchaView
)

app_name = 'system'

router = DefaultRouter()
router.register('login-logs', LoginLogViewSet, basename='login-log')
router.register('operation-logs', OperationLogViewSet, basename='operation-log')
router.register('departments', DepartmentViewSet, basename='department')
router.register('menus', MenuViewSet, basename='menu')
router.register('permissions', RolePermissionViewSet, basename='permission')

urlpatterns = [
    path('captcha/', CaptchaView.as_view(), name='captcha'),
    path('', include(router.urls)),
]
