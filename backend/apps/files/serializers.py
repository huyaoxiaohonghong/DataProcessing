"""
文件序列化器
Serializers for File model
"""
from rest_framework import serializers
from .models import File, FileCategory


class FileCategorySerializer(serializers.ModelSerializer):
    """文件分类序列化器"""
    children_count = serializers.IntegerField(read_only=True)
    files_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = FileCategory
        fields = [
            'id', 'name', 'description', 'parent',
            'children_count', 'files_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


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
    
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    class Meta:
        model = File
        fields = ['name', 'description', 'file', 'category', 'department', 'tags', 'is_public']
        extra_kwargs = {
            'name': {'required': False}
        }
    
    def validate_file(self, value):
        # 文件类型白名单校验
        ext = value.name.rsplit('.', 1)[-1].lower() if '.' in value.name else ''
        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(f'不支持的文件类型: {ext}')
        # 文件大小限制
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError('文件大小不能超过 50MB')
        return value
    
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
