"""
数据处理 URL 配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataMappingViewSet, ProcessingTaskViewSet

app_name = 'processing'

router = DefaultRouter()
router.register('mappings', DataMappingViewSet, basename='mapping')
router.register('tasks', ProcessingTaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
