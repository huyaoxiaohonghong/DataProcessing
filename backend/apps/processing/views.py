"""
数据处理视图
Views for data processing, mapping and tasks
"""
import logging

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import DataMapping, MappingField, ProcessingTask
from .serializers import (
    DataMappingSerializer, DataMappingCreateSerializer,
    DataMappingListSerializer,
    MappingFieldSerializer, ProcessingTaskSerializer, 
    ProcessingTaskCreateSerializer
)
from .services import ExcelService
from .tasks import execute_processing_task
from config.celery import app as celery_app
from apps.files.models import File
from utils.response import ApiResponse

logger = logging.getLogger('apps')


class DataMappingViewSet(viewsets.ModelViewSet):
    """数据映射配置视图"""
    queryset = DataMapping.objects.select_related(
        'source_file', 'reference_file', 'target_template', 'created_by'
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DataMappingCreateSerializer
        if self.action == 'list':
            return DataMappingListSerializer
        return DataMappingSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'super_admin':
            return qs
        return qs.filter(created_by=user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        result_serializer = DataMappingSerializer(serializer.instance)
        return ApiResponse.created(result_serializer.data, '创建成功')
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        result_serializer = DataMappingSerializer(instance)
        return ApiResponse.success(result_serializer.data, '更新成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.tasks.exists():
            return ApiResponse.error('存在关联任务，无法删除')
        self.perform_destroy(instance)
        return ApiResponse.success(message='删除成功')
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活配置"""
        instance = self.get_object()
        if not instance.fields.exists():
            return ApiResponse.error('请先配置字段映射')
        
        instance.status = 'active'
        instance.save(update_fields=['status', 'updated_at'])
        return ApiResponse.success(message='激活成功')
    
    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用配置"""
        instance = self.get_object()
        instance.status = 'disabled'
        instance.save(update_fields=['status', 'updated_at'])
        return ApiResponse.success(message='禁用成功')
    
    @action(detail=False, methods=['post'])
    def parse_file(self, request):
        """解析文件字段"""
        file_id = request.data.get('file_id')
        if not file_id:
            return ApiResponse.error('请提供文件ID')
        
        try:
            file_obj = File.objects.get(id=file_id)
            sheets = ExcelService.parse_file_fields(file_obj)
            return ApiResponse.success({
                'file_id': file_id,
                'file_name': file_obj.name,
                'sheets': sheets
            }, '解析成功')
        except File.DoesNotExist:
            return ApiResponse.not_found('文件不存在')
        except Exception as e:
            logger.exception(f"解析文件失败: file_id={file_id}")
            return ApiResponse.server_error(str(e))


class ProcessingTaskViewSet(viewsets.ModelViewSet):
    """处理任务视图"""
    queryset = ProcessingTask.objects.select_related('mapping', 'created_by').all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'mapping', 'created_by']
    search_fields = ['name']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProcessingTaskCreateSerializer
        return ProcessingTaskSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'super_admin':
            return qs
        return qs.filter(created_by=user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        result_serializer = ProcessingTaskSerializer(serializer.instance)
        return ApiResponse.created(result_serializer.data, '任务创建成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == 'running':
            return ApiResponse.error('任务正在执行，无法删除')
        self.perform_destroy(instance)
        return ApiResponse.success(message='删除成功')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行任务（异步提交到 Celery）"""
        task = self.get_object()
        
        if task.status not in ['pending', 'failed']:
            return ApiResponse.error('任务状态不允许执行')
        
        task.status = 'pending'
        task.save(update_fields=['status'])
        execute_processing_task.delay(task.id)
        return ApiResponse.success({'task_id': task.id}, '任务已提交')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消任务（待执行状态）"""
        task = self.get_object()
        
        if task.status != 'pending':
            return ApiResponse.error('只能取消待执行的任务')
        
        task.status = 'cancelled'
        task.save(update_fields=['status'])
        return ApiResponse.success(message='取消成功')
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """终止任务（运行中状态）"""
        task = self.get_object()
        
        if task.status != 'running':
            return ApiResponse.error('只能终止运行中的任务')
        
        # 通过 Celery revoke 终止异步任务
        if task.celery_task_id:
            celery_app.control.revoke(task.celery_task_id, terminate=True)
        
        task.status = 'cancelled'
        task.error_message = '任务被用户手动终止'
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'completed_at'])
        
        serializer = self.get_serializer(task)
        return ApiResponse.success(serializer.data, '任务已终止')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载结果文件"""
        task = self.get_object()

        if not task.result_file:
            return ApiResponse.not_found('结果文件不存在')

        from django.conf import settings

        if getattr(settings, 'USE_S3', False):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(task.result_file.url)
        else:
            response = FileResponse(
                task.result_file.open('rb'),
                as_attachment=True,
                filename=f"{task.name}_result.xlsx"
            )
            return response
