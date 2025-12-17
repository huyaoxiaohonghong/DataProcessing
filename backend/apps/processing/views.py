"""
数据处理视图
Views for data processing, mapping and tasks
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import DataMapping, MappingField, ProcessingTask
from .serializers import (
    DataMappingSerializer, DataMappingCreateSerializer,
    MappingFieldSerializer, ProcessingTaskSerializer, 
    ProcessingTaskCreateSerializer
)
from .services import ExcelService, DataProcessingService
from apps.files.models import File


class DataMappingViewSet(viewsets.ModelViewSet):
    """数据映射配置视图"""
    queryset = DataMapping.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DataMappingCreateSerializer
        return DataMappingSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return DataMapping.objects.all()
        return DataMapping.objects.filter(created_by=user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
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
        
        result_serializer = DataMappingSerializer(serializer.instance)
        return Response({
            'code': 200,
            'message': '创建成功',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        result_serializer = DataMappingSerializer(instance)
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': result_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.tasks.exists():
            return Response({
                'code': 400,
                'message': '存在关联任务，无法删除'
            }, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response({
            'code': 200,
            'message': '删除成功'
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活配置"""
        instance = self.get_object()
        if not instance.fields.exists():
            return Response({
                'code': 400,
                'message': '请先配置字段映射'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        instance.status = 'active'
        instance.save()
        return Response({
            'code': 200,
            'message': '激活成功'
        })
    
    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用配置"""
        instance = self.get_object()
        instance.status = 'disabled'
        instance.save()
        return Response({
            'code': 200,
            'message': '禁用成功'
        })
    
    @action(detail=False, methods=['post'])
    def parse_file(self, request):
        """解析文件字段"""
        file_id = request.data.get('file_id')
        if not file_id:
            return Response({
                'code': 400,
                'message': '请提供文件ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            file_obj = File.objects.get(id=file_id)
            sheets = ExcelService.parse_file_fields(file_obj)
            return Response({
                'code': 200,
                'message': '解析成功',
                'data': {
                    'file_id': file_id,
                    'file_name': file_obj.name,
                    'sheets': sheets
                }
            })
        except File.DoesNotExist:
            return Response({
                'code': 404,
                'message': '文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'code': 500,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessingTaskViewSet(viewsets.ModelViewSet):
    """处理任务视图"""
    queryset = ProcessingTask.objects.all()
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
        user = self.request.user
        if user.role == 'super_admin':
            return ProcessingTask.objects.all()
        return ProcessingTask.objects.filter(created_by=user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
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
        
        result_serializer = ProcessingTaskSerializer(serializer.instance)
        return Response({
            'code': 200,
            'message': '任务创建成功',
            'data': result_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == 'running':
            return Response({
                'code': 400,
                'message': '任务正在执行，无法删除'
            }, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response({
            'code': 200,
            'message': '删除成功'
        })
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行任务"""
        task = self.get_object()
        
        if task.status not in ['pending', 'failed']:
            return Response({
                'code': 400,
                'message': '任务状态不允许执行'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 同步执行（实际项目中应使用 Celery 异步执行）
        success = DataProcessingService.execute_task(task)
        
        task.refresh_from_db()
        serializer = self.get_serializer(task)
        
        return Response({
            'code': 200 if success else 500,
            'message': '执行成功' if success else f'执行失败: {task.error_message}',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消任务（待执行状态）"""
        task = self.get_object()
        
        if task.status != 'pending':
            return Response({
                'code': 400,
                'message': '只能取消待执行的任务'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'cancelled'
        task.save()
        
        return Response({
            'code': 200,
            'message': '取消成功'
        })
    
    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """终止任务（运行中状态）"""
        task = self.get_object()
        
        if task.status != 'running':
            return Response({
                'code': 400,
                'message': '只能终止运行中的任务'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 标记任务为已取消
        task.status = 'cancelled'
        task.error_message = '任务被用户手动终止'
        task.completed_at = timezone.now()
        task.save()
        
        serializer = self.get_serializer(task)
        return Response({
            'code': 200,
            'message': '任务已终止',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载结果文件"""
        task = self.get_object()
        
        if not task.result_file:
            return Response({
                'code': 404,
                'message': '结果文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        response = FileResponse(
            task.result_file.open('rb'),
            as_attachment=True,
            filename=f"{task.name}_result.xlsx"
        )
        return response
