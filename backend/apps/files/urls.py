"""
文件模块 URL 配置
URL patterns for files app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FileViewSet, FileCategoryViewSet

app_name = 'files'

router = DefaultRouter()
router.register('categories', FileCategoryViewSet, basename='category')
router.register('', FileViewSet, basename='file')

urlpatterns = [
    path('', include(router.urls)),
]
