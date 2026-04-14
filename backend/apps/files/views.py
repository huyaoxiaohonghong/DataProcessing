"""
文件视图
Views for File management with upload/download
"""
import logging

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from django.db.models import Q, F, Count, Sum, Value
from django.db.models.functions import Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import File, FileCategory
from .serializers import (
    FileSerializer,
    FileUploadSerializer,
    FileUpdateSerializer,
    FileCategorySerializer
)
from apps.system.cache import CacheService
from utils.response import ApiResponse

logger = logging.getLogger('apps')


class FileCategoryViewSet(viewsets.ModelViewSet):
    """文件分类 CRUD"""
    serializer_class = FileCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        return FileCategory.objects.annotate(
            children_count=Count('children'),
            files_count=Count('files', filter=Q(files__status='active'))
        )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        CacheService.clear_file_cache()
        return ApiResponse.created(serializer.data, '创建成功')
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        CacheService.clear_file_cache()
        return ApiResponse.success(serializer.data, '更新成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        CacheService.clear_file_cache()
        return ApiResponse.success(message='删除成功')


class FileViewSet(viewsets.ModelViewSet):
    """文件 CRUD + 上传/下载"""
    queryset = File.objects.select_related(
        'uploaded_by', 'category', 'department'
    ).filter(status='active')
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'status', 'file_type', 'is_public', 'uploaded_by']
    search_fields = ['name', 'original_name', 'description', 'tags']
    ordering_fields = ['name', 'file_size', 'created_at', 'download_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FileUploadSerializer
        elif self.action in ['update', 'partial_update']:
            return FileUpdateSerializer
        return FileSerializer
    
    def get_queryset(self):
        """根据角色过滤文件"""
        user = self.request.user
        queryset = File.objects.select_related('uploaded_by', 'category', 'department')
        
        if user.role == 'super_admin':
            pass
        elif user.role == 'admin':
            queryset = queryset.filter(
                Q(uploaded_by=user) | 
                Q(department=user.department) | 
                Q(is_public=True)
            )
        else:
            queryset = queryset.filter(
                Q(uploaded_by=user) | Q(is_public=True)
            )
        
        if self.action == 'list':
            queryset = queryset.exclude(status='deleted')
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        CacheService.clear_file_cache()
        
        file_serializer = FileSerializer(serializer.instance)
        return ApiResponse.created(file_serializer.data, '上传成功')
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        CacheService.clear_file_cache()
        
        file_serializer = FileSerializer(instance)
        return ApiResponse.success(file_serializer.data, '更新成功')
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = 'deleted'
        instance.save(update_fields=['status', 'updated_at'])
        CacheService.clear_file_cache()
        return ApiResponse.success(message='删除成功')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """文件下载"""
        try:
            file_obj = self.get_object()

            if not file_obj.file:
                return ApiResponse.not_found('文件不存在')

            # 使用 F() 原子更新下载计数，避免竞态条件
            File.objects.filter(pk=file_obj.pk).update(download_count=F('download_count') + 1)

            from django.conf import settings

            if getattr(settings, 'USE_S3', False):
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(file_obj.file.url)
            else:
                return FileResponse(
                    file_obj.file.open('rb'),
                    as_attachment=True,
                    filename=file_obj.original_name or file_obj.name
                )

        except Exception as e:
            logger.exception(f"文件下载失败: file_id={pk}")
            return ApiResponse.server_error(f'下载失败: {str(e)}')
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """文件统计"""
        queryset = self.get_queryset().filter(status='active')

        totals = queryset.aggregate(
            total_files=Count('id'),
            total_size=Coalesce(Sum('file_size'), 0),
            total_downloads=Coalesce(Sum('download_count'), 0),
        )

        type_stats_qs = (
            queryset
            .values(file_type_key=Coalesce('file_type', Value('unknown')))
            .annotate(count=Count('id'), size=Coalesce(Sum('file_size'), 0))
            .order_by('-count')
        )
        type_stats = {
            item['file_type_key']: {'count': item['count'], 'size': item['size']}
            for item in type_stats_qs
        }

        return ApiResponse.success({**totals, 'type_stats': type_stats})
