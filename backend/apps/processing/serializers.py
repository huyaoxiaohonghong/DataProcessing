"""
数据处理序列化器
Serializers for data processing
"""
from rest_framework import serializers
from .models import DataMapping, MappingField, ProcessingTask


class MappingFieldSerializer(serializers.ModelSerializer):
    """字段映射序列化器"""
    field_type_display = serializers.CharField(source='get_field_type_display', read_only=True)
    
    class Meta:
        model = MappingField
        fields = [
            'id', 'source_field', 'source_field_index',
            'reference_sheet', 'reference_name_column', 'reference_code_column',
            'reference_field', 'reference_field_index',
            'target_field', 'target_field_index',
            'field_type', 'field_type_display',
            'default_value', 'compute_expression',
            'transform_rule', 'sort_order'
        ]


class DataMappingSerializer(serializers.ModelSerializer):
    """数据映射配置序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    source_file_name = serializers.SerializerMethodField()
    reference_file_name = serializers.SerializerMethodField()
    target_template_name = serializers.SerializerMethodField()
    fields = MappingFieldSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    
    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else None
    
    def get_source_file_name(self, obj):
        return obj.source_file.name if obj.source_file else None
    
    def get_reference_file_name(self, obj):
        return obj.reference_file.name if obj.reference_file else None
    
    def get_target_template_name(self, obj):
        return obj.target_template.name if obj.target_template else None
    
    class Meta:
        model = DataMapping
        fields = [
            'id', 'name', 'description',
            'source_file', 'source_file_name', 'source_sheet',
            'reference_file', 'reference_file_name', 'reference_sheet',
            'target_template', 'target_template_name', 'target_sheet',
            'status', 'status_display',
            'fields', 'task_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_task_count(self, obj):
        return obj.tasks.count()


class DataMappingCreateSerializer(serializers.ModelSerializer):
    """创建数据映射配置序列化器"""
    fields = MappingFieldSerializer(many=True, required=False)
    
    class Meta:
        model = DataMapping
        fields = [
            'name', 'description',
            'source_file', 'source_sheet',
            'reference_file', 'reference_sheet',
            'target_template', 'target_sheet',
            'status', 'fields'
        ]
    
    def create(self, validated_data):
        fields_data = validated_data.pop('fields', [])
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        mapping = DataMapping.objects.create(**validated_data)
        
        # 创建字段映射
        for i, field_data in enumerate(fields_data):
            field_data['sort_order'] = i
            MappingField.objects.create(mapping=mapping, **field_data)
        
        return mapping
    
    def update(self, instance, validated_data):
        fields_data = validated_data.pop('fields', None)
        
        # 更新映射配置
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 如果提供了字段数据，则更新字段
        if fields_data is not None:
            # 删除旧字段
            instance.fields.all().delete()
            # 创建新字段
            for i, field_data in enumerate(fields_data):
                field_data['sort_order'] = i
                MappingField.objects.create(mapping=instance, **field_data)
        
        return instance


class ProcessingTaskSerializer(serializers.ModelSerializer):
    """处理任务序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    mapping_name = serializers.CharField(source='mapping.name', read_only=True)
    progress = serializers.ReadOnlyField()
    
    class Meta:
        model = ProcessingTask
        fields = [
            'id', 'name', 'mapping', 'mapping_name',
            'status', 'status_display',
            'started_at', 'completed_at',
            'total_rows', 'processed_rows', 'success_rows', 'error_rows',
            'progress', 'result_file', 'error_message',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'started_at', 'completed_at',
            'total_rows', 'processed_rows', 'success_rows', 'error_rows',
            'result_file', 'error_message', 'created_by', 'created_at'
        ]


class ProcessingTaskCreateSerializer(serializers.ModelSerializer):
    """创建处理任务序列化器"""
    
    class Meta:
        model = ProcessingTask
        fields = ['name', 'mapping']
    
    def validate_mapping(self, value):
        if value.status != 'active':
            raise serializers.ValidationError('只能基于已激活的配置创建任务')
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class FileFieldsSerializer(serializers.Serializer):
    """文件字段解析结果序列化器"""
    file_id = serializers.IntegerField()
    file_name = serializers.CharField()
    sheets = serializers.ListField(child=serializers.DictField())
