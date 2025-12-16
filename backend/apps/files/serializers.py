"""
文件序列化器
Serializers for File model
"""
from rest_framework import serializers
from .models import File, FileCategory


class FileCategorySerializer(serializers.ModelSerializer):
    """文件分类序列化器"""
    children_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FileCategory
        fields = [
            'id', 'name', 'description', 'parent',
            'children_count', 'files_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_files_count(self, obj):
        return obj.files.filter(status='active').count()


class FileSerializer(serializers.ModelSerializer):
    """文件序列化器"""
    file_size_display = serializers.ReadOnlyField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = File
        fields = [
            'id', 'name', 'original_name', 'description',
            'file', 'file_size', 'file_size_display', 'file_type', 'mime_type',
            'category', 'category_name', 'tags',
            'status', 'status_display', 'is_public',
            'uploaded_by', 'uploaded_by_name', 'department', 'department_name', 'download_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'file_type', 'mime_type',
            'uploaded_by', 'download_count', 'created_at', 'updated_at'
        ]


class FileUploadSerializer(serializers.ModelSerializer):
    """文件上传序列化器"""
    
    class Meta:
        model = File
        fields = ['name', 'description', 'file', 'category', 'department', 'tags', 'is_public']
        extra_kwargs = {
            'name': {'required': False}
        }
    
    def create(self, validated_data):
        # 自动填充文件信息
        file_obj = validated_data.get('file')
        if file_obj:
            if not validated_data.get('name'):
                validated_data['name'] = file_obj.name
            validated_data['original_name'] = file_obj.name
            validated_data['file_size'] = file_obj.size
            validated_data['mime_type'] = getattr(file_obj, 'content_type', '')
            
            # 获取文件扩展名
            ext = file_obj.name.split('.')[-1].lower() if '.' in file_obj.name else ''
            validated_data['file_type'] = ext
        
        # 设置上传者和部门
        request = self.context.get('request')
        if request and request.user:
            validated_data['uploaded_by'] = request.user
            # 如果没有指定部门，使用用户所属部门
            if not validated_data.get('department') and hasattr(request.user, 'department'):
                validated_data['department'] = request.user.department
        
        return super().create(validated_data)


class FileUpdateSerializer(serializers.ModelSerializer):
    """文件更新序列化器"""
    
    class Meta:
        model = File
        fields = ['name', 'description', 'category', 'department', 'tags', 'is_public', 'status']
