"""
文件视图
Views for File management with upload/download
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import File, FileCategory
from .serializers import (
    FileSerializer,
    FileUploadSerializer,
    FileUpdateSerializer,
    FileCategorySerializer
)
from apps.system.cache import CacheService, CacheKeys


class FileCategoryViewSet(viewsets.ModelViewSet):
    """
    文件分类 CRUD
    """
    queryset = FileCategory.objects.all()
    serializer_class = FileCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
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
        # 清除文件缓存
        CacheService.clear_file_cache()
        return Response({
            'code': 200,
            'message': '创建成功',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # 清除文件缓存
        CacheService.clear_file_cache()
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        # 清除文件缓存
        CacheService.clear_file_cache()
        return Response({
            'code': 200,
            'message': '删除成功'
        })


class FileViewSet(viewsets.ModelViewSet):
    """
    文件 CRUD + 上传/下载
    """
    queryset = File.objects.filter(status='active')
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
        queryset = File.objects.all()
        
        if user.role == 'super_admin':
            # 超级管理员可以看到所有文件
            pass
        elif user.role == 'admin':
            # 管理员可以看到自己的文件、同部门文件和公开文件
            queryset = queryset.filter(
                Q(uploaded_by=user) | 
                Q(department=user.department) | 
                Q(is_public=True)
            )
        else:
            # 普通用户只能看到自己的文件和公开文件
            queryset = queryset.filter(
                Q(uploaded_by=user) | Q(is_public=True)
            )
        
        # 默认不显示已删除的文件
        if self.action == 'list':
            queryset = queryset.exclude(status='deleted')
        return queryset
    
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
        
        # 清除文件缓存
        CacheService.clear_file_cache()
        
        # 返回完整的文件信息
        file_serializer = FileSerializer(serializer.instance)
        return Response({
            'code': 200,
            'message': '上传成功',
            'data': file_serializer.data
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
        
        # 清除文件缓存
        CacheService.clear_file_cache()
        
        file_serializer = FileSerializer(instance)
        return Response({
            'code': 200,
            'message': '更新成功',
            'data': file_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # 软删除
        instance.status = 'deleted'
        instance.save()
        # 清除文件缓存
        CacheService.clear_file_cache()
        return Response({
            'code': 200,
            'message': '删除成功'
        })
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download(self, request, pk=None):
        """
        文件下载
        GET /api/files/{id}/download/
        """
        try:
            file_obj = self.get_object()
            
            if not file_obj.file:
                return Response({
                    'code': 404,
                    'message': '文件不存在'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 增加下载计数
            file_obj.download_count += 1
            file_obj.save(update_fields=['download_count'])
            
            # 返回文件响应
            response = FileResponse(
                file_obj.file.open('rb'),
                as_attachment=True,
                filename=file_obj.original_name or file_obj.name
            )
            return response
            
        except Exception as e:
            return Response({
                'code': 500,
                'message': f'下载失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        文件统计
        GET /api/files/statistics/
        """
        queryset = self.get_queryset().filter(status='active')
        total_files = queryset.count()
        total_size = sum(f.file_size for f in queryset)
        total_downloads = sum(f.download_count for f in queryset)
        
        # 按类型统计
        type_stats = {}
        for f in queryset:
            ft = f.file_type or 'unknown'
            if ft not in type_stats:
                type_stats[ft] = {'count': 0, 'size': 0}
            type_stats[ft]['count'] += 1
            type_stats[ft]['size'] += f.file_size
        
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'total_files': total_files,
                'total_size': total_size,
                'total_downloads': total_downloads,
                'type_stats': type_stats
            }
        })
