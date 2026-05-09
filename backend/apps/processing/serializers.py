"""
数据处理序列化器
Serializers for data processing
"""
from rest_framework import serializers
from django.db import transaction
from .models import (
    DataMapping, MappingField, MappingTargetSheet,
    SheetLineage, FieldLineage,
    ProcessingTask, TaskSheetResult,
)


class MappingFieldSerializer(serializers.ModelSerializer):
    """字段映射序列化器"""
    field_type_display = serializers.CharField(source='get_field_type_display', read_only=True)

    class Meta:
        model = MappingField
        fields = [
            'id', 'target_sheet_config',
            'source_field', 'source_field_index',
            'reference_sheet', 'reference_name_column', 'reference_code_column',
            'reference_field', 'reference_field_index',
            'target_field', 'target_field_index',
            'field_type', 'field_type_display',
            'default_value', 'compute_expression',
            'source_target_sheet', 'source_target_field', 'aggregation',
            'transform_rule', 'sort_order',
        ]


class MappingTargetSheetSerializer(serializers.ModelSerializer):
    """目标 Sheet 配置序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fields = MappingFieldSerializer(many=True, read_only=True)
    field_count = serializers.SerializerMethodField()

    class Meta:
        model = MappingTargetSheet
        fields = [
            'id', 'sheet_name', 'display_name', 'description',
            'status', 'status_display',
            'source_sheet', 'sort_order',
            'fields', 'field_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_field_count(self, obj):
        return obj.fields.count()


class SheetLineageSerializer(serializers.ModelSerializer):
    """Sheet 血缘序列化器"""
    relation_type_display = serializers.CharField(source='get_relation_type_display', read_only=True)
    upstream_name = serializers.CharField(source='upstream.sheet_name', read_only=True)
    downstream_name = serializers.CharField(source='downstream.sheet_name', read_only=True)

    class Meta:
        model = SheetLineage
        fields = [
            'id', 'upstream', 'upstream_name',
            'downstream', 'downstream_name',
            'relation_type', 'relation_type_display',
            'join_keys', 'description',
        ]


class FieldLineageSerializer(serializers.ModelSerializer):
    """字段血缘序列化器"""
    upstream_sheet_name = serializers.CharField(source='upstream_sheet.sheet_name', read_only=True)
    downstream_sheet_name = serializers.CharField(source='downstream_sheet.sheet_name', read_only=True)

    class Meta:
        model = FieldLineage
        fields = [
            'id',
            'upstream_sheet', 'upstream_sheet_name', 'upstream_field',
            'downstream_sheet', 'downstream_sheet_name', 'downstream_field',
            'transform', 'note',
        ]


class DataMappingListSerializer(serializers.ModelSerializer):
    """数据映射列表序列化器（轻量，不含 fields 详情）"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', default=None, read_only=True)
    source_file_name = serializers.CharField(source='source_file.name', default=None, read_only=True)
    reference_file_name = serializers.CharField(source='reference_file.name', default=None, read_only=True)
    target_template_name = serializers.CharField(source='target_template.name', default=None, read_only=True)
    target_sheet_count = serializers.SerializerMethodField()

    class Meta:
        model = DataMapping
        fields = [
            'id', 'name', 'description',
            'source_file', 'source_file_name', 'source_sheet',
            'reference_file', 'reference_file_name', 'reference_sheet',
            'target_template', 'target_template_name', 'target_sheet',
            'target_sheet_count',
            'status', 'status_display',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_target_sheet_count(self, obj):
        return obj.target_sheets.count()


class DataMappingSerializer(serializers.ModelSerializer):
    """数据映射配置详情序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', default=None, read_only=True)
    source_file_name = serializers.CharField(source='source_file.name', default=None, read_only=True)
    reference_file_name = serializers.CharField(source='reference_file.name', default=None, read_only=True)
    target_template_name = serializers.CharField(source='target_template.name', default=None, read_only=True)
    fields = MappingFieldSerializer(many=True, read_only=True)
    target_sheets = MappingTargetSheetSerializer(many=True, read_only=True)
    sheet_lineages = SheetLineageSerializer(many=True, read_only=True)
    field_lineages = FieldLineageSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = DataMapping
        fields = [
            'id', 'name', 'description',
            'source_file', 'source_file_name', 'source_sheet',
            'reference_file', 'reference_file_name', 'reference_sheet',
            'target_template', 'target_template_name', 'target_sheet',
            'status', 'status_display',
            'fields', 'target_sheets', 'sheet_lineages', 'field_lineages',
            'task_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_task_count(self, obj):
        return obj.tasks.count()


# --- 写入用 嵌套序列化器 ---------------------------------------------------

class _SheetLineageWriteSerializer(serializers.Serializer):
    """写入时使用的血缘条目：upstream / downstream 用 sheet_name（字符串）指向。"""
    upstream = serializers.CharField(max_length=100)
    downstream = serializers.CharField(max_length=100)
    relation_type = serializers.ChoiceField(
        choices=SheetLineage.RelationType.choices,
        default=SheetLineage.RelationType.DERIVED,
    )
    join_keys = serializers.JSONField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default='')


class _FieldLineageWriteSerializer(serializers.Serializer):
    upstream_sheet = serializers.CharField(max_length=100)
    upstream_field = serializers.CharField(max_length=200)
    downstream_sheet = serializers.CharField(max_length=100)
    downstream_field = serializers.CharField(max_length=200)
    # Req 4.3: transform 限定为 direct/computed/aggregated/lookup
    transform = serializers.ChoiceField(
        choices=[
            ('direct', 'direct'),
            ('computed', 'computed'),
            ('aggregated', 'aggregated'),
            ('lookup', 'lookup'),
        ],
        default='direct',
    )
    note = serializers.CharField(required=False, allow_blank=True, default='')


class _MappingFieldWriteSerializer(serializers.Serializer):
    """写入字段映射。target_sheet_name 用于关联到目标 sheet（通过名称匹配）。"""
    target_sheet_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')

    source_field = serializers.CharField(max_length=200, allow_blank=True, required=False, default='')
    source_field_index = serializers.IntegerField(default=-1)

    reference_sheet = serializers.CharField(max_length=100, allow_blank=True, required=False, default='')
    reference_name_column = serializers.CharField(max_length=200, allow_blank=True, required=False, default='')
    reference_code_column = serializers.CharField(max_length=200, allow_blank=True, required=False, default='')
    reference_field = serializers.CharField(max_length=200, allow_blank=True, required=False, default='')
    reference_field_index = serializers.IntegerField(default=-1)

    target_field = serializers.CharField(max_length=200)
    target_field_index = serializers.IntegerField(default=-1)

    field_type = serializers.ChoiceField(
        choices=MappingField.FieldType.choices,
        default=MappingField.FieldType.DIRECT,
    )
    default_value = serializers.CharField(max_length=500, allow_blank=True, required=False, default='')
    compute_expression = serializers.CharField(max_length=500, allow_blank=True, required=False, default='')

    # 跨 sheet 引用字段（upstream sheet 用名称）
    source_target_sheet_name = serializers.CharField(max_length=100, allow_blank=True, required=False, default='')
    source_target_field = serializers.CharField(max_length=200, allow_blank=True, required=False, default='')
    # Req 6.4: aggregation 限定为 '' / sum / count / avg / min / max / first
    aggregation = serializers.ChoiceField(
        choices=[
            ('', ''),
            ('sum', 'sum'),
            ('count', 'count'),
            ('avg', 'avg'),
            ('min', 'min'),
            ('max', 'max'),
            ('first', 'first'),
        ],
        required=False, allow_blank=True, default='',
    )

    transform_rule = serializers.JSONField(required=False, allow_null=True)
    sort_order = serializers.IntegerField(default=0)


class _MappingTargetSheetWriteSerializer(serializers.Serializer):
    sheet_name = serializers.CharField(max_length=100)
    display_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
    description = serializers.CharField(required=False, allow_blank=True, default='')
    status = serializers.ChoiceField(
        choices=MappingTargetSheet.Status.choices,
        default=MappingTargetSheet.Status.DRAFT,
    )
    source_sheet = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')
    sort_order = serializers.IntegerField(default=0)
    fields = _MappingFieldWriteSerializer(many=True, required=False)


class DataMappingCreateSerializer(serializers.ModelSerializer):
    """创建/更新数据映射配置序列化器

    支持两种模式：
      - 单 sheet 兼容模式：传 target_sheet + fields（老结构）
      - 多 sheet 模式：传 target_sheets（每个含自己的 fields） + sheet_lineages + field_lineages

    两种模式可以并存（若同时给了 target_sheets，它会优先生效）。
    """
    fields = MappingFieldSerializer(many=True, required=False)
    target_sheets = _MappingTargetSheetWriteSerializer(many=True, required=False)
    sheet_lineages = _SheetLineageWriteSerializer(many=True, required=False)
    field_lineages = _FieldLineageWriteSerializer(many=True, required=False)

    class Meta:
        model = DataMapping
        fields = [
            'name', 'description',
            'source_file', 'source_sheet',
            'reference_file', 'reference_sheet',
            'target_template', 'target_sheet',
            'status', 'fields',
            'target_sheets', 'sheet_lineages', 'field_lineages',
        ]

    def validate(self, attrs):
        """Req 1.3 / 3.3 / 3.5：结构性硬错误（Stage A），不落库。"""
        from .lineage_validator import validate_structural, collect_unknown_refs

        target_sheets_data = attrs.get('target_sheets') or []
        sheet_lineages_data = attrs.get('sheet_lineages') or []
        field_lineages_data = attrs.get('field_lineages') or []

        validate_structural(target_sheets_data, sheet_lineages_data, field_lineages_data)

        # 收集非致命告警（Req 3.2 / 4.2 / 6.3），供视图层拼到响应 warnings[]
        warnings = collect_unknown_refs(
            target_sheets_data, sheet_lineages_data, field_lineages_data,
        )
        self.context['warnings'] = warnings
        return attrs

    def _rebuild_children(self, mapping, target_sheets_data, legacy_fields_data,
                          sheet_lineages_data, field_lineages_data):
        """重建所有子对象（先删后建）"""
        mapping.fields.all().delete()
        mapping.target_sheets.all().delete()  # 级联会删除 lineage / field
        mapping.sheet_lineages.all().delete()
        mapping.field_lineages.all().delete()

        # 1) 目标 sheet（多 sheet 模式）
        sheet_by_name = {}
        # 缓存 (sheet_obj, fields_data) 便于二轮回填跨 sheet 引用
        pending_sheets = []
        if target_sheets_data:
            for order, ts in enumerate(target_sheets_data):
                fields_data = ts.pop('fields', [])
                ts_obj = MappingTargetSheet.objects.create(
                    mapping=mapping,
                    sheet_name=ts['sheet_name'],
                    display_name=ts.get('display_name', ''),
                    description=ts.get('description', ''),
                    status=ts.get('status', MappingTargetSheet.Status.DRAFT),
                    source_sheet=ts.get('source_sheet', ''),
                    sort_order=ts.get('sort_order', order),
                )
                sheet_by_name[ts_obj.sheet_name] = ts_obj
                pending_sheets.append((ts_obj, fields_data))

            # 第一轮：建字段（跨 sheet 引用 FK 暂为空，稍后回填）
            created_field_pairs = []  # (MappingField, fd)
            for ts_obj, fields_data in pending_sheets:
                for i, fd in enumerate(fields_data):
                    mf = MappingField.objects.create(
                        mapping=mapping,
                        target_sheet_config=ts_obj,
                        source_field=fd.get('source_field', ''),
                        source_field_index=fd.get('source_field_index', -1),
                        reference_sheet=fd.get('reference_sheet', ''),
                        reference_name_column=fd.get('reference_name_column', ''),
                        reference_code_column=fd.get('reference_code_column', ''),
                        reference_field=fd.get('reference_field', ''),
                        reference_field_index=fd.get('reference_field_index', -1),
                        target_field=fd['target_field'],
                        target_field_index=fd.get('target_field_index', -1),
                        field_type=fd.get('field_type', MappingField.FieldType.DIRECT),
                        default_value=fd.get('default_value', ''),
                        compute_expression=fd.get('compute_expression', ''),
                        source_target_field=fd.get('source_target_field', ''),
                        aggregation=fd.get('aggregation', ''),
                        transform_rule=fd.get('transform_rule'),
                        sort_order=fd.get('sort_order', i),
                    )
                    created_field_pairs.append((mf, fd))

            # 第二轮：回填 source_target_sheet（需要 sheet_by_name 已建齐）
            to_update = []
            for mf, fd in created_field_pairs:
                ref_name = fd.get('source_target_sheet_name', '')
                if not ref_name:
                    continue
                upstream = sheet_by_name.get(ref_name)
                if not upstream:
                    continue
                mf.source_target_sheet = upstream
                to_update.append(mf)
            if to_update:
                MappingField.objects.bulk_update(to_update, ['source_target_sheet'])

        # 2) 旧版 / 兼容模式字段（只在没有 target_sheets 时启用）
        if not target_sheets_data and legacy_fields_data:
            MappingField.objects.bulk_create([
                MappingField(mapping=mapping, **{**fd, 'sort_order': i})
                for i, fd in enumerate(legacy_fields_data)
            ])

        # 3) Sheet 血缘
        if sheet_lineages_data and sheet_by_name:
            seen_triples: set = set()
            for sl in sheet_lineages_data:
                upstream = sheet_by_name.get(sl['upstream'])
                downstream = sheet_by_name.get(sl['downstream'])
                if not upstream or not downstream:
                    continue
                # Req 3.5 DB 兜底：跳过已存在的三元组
                relation_type = sl.get('relation_type', SheetLineage.RelationType.DERIVED)
                triple = (upstream.id, downstream.id, relation_type)
                if triple in seen_triples:
                    continue
                seen_triples.add(triple)
                SheetLineage.objects.create(
                    mapping=mapping,
                    upstream=upstream,
                    downstream=downstream,
                    relation_type=relation_type,
                    join_keys=sl.get('join_keys'),
                    description=sl.get('description', ''),
                )

        # 4) Field 血缘
        if field_lineages_data and sheet_by_name:
            for fl in field_lineages_data:
                us = sheet_by_name.get(fl['upstream_sheet'])
                ds = sheet_by_name.get(fl['downstream_sheet'])
                if not us or not ds:
                    continue
                FieldLineage.objects.create(
                    mapping=mapping,
                    upstream_sheet=us,
                    upstream_field=fl['upstream_field'],
                    downstream_sheet=ds,
                    downstream_field=fl['downstream_field'],
                    transform=fl.get('transform', 'direct'),
                    note=fl.get('note', ''),
                )

    def create(self, validated_data):
        fields_data = validated_data.pop('fields', [])
        target_sheets_data = validated_data.pop('target_sheets', [])
        sheet_lineages_data = validated_data.pop('sheet_lineages', [])
        field_lineages_data = validated_data.pop('field_lineages', [])

        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user

        with transaction.atomic():
            mapping = DataMapping.objects.create(**validated_data)
            self._rebuild_children(
                mapping, target_sheets_data, fields_data,
                sheet_lineages_data, field_lineages_data,
            )
        return mapping

    def update(self, instance, validated_data):
        fields_data = validated_data.pop('fields', None)
        target_sheets_data = validated_data.pop('target_sheets', None)
        sheet_lineages_data = validated_data.pop('sheet_lineages', None)
        field_lineages_data = validated_data.pop('field_lineages', None)

        with transaction.atomic():
            # Req 1.5 并发安全：对 DataMapping 加 select_for_update 防止并发 rebuild
            instance = DataMapping.objects.select_for_update().get(pk=instance.pk)
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # 只要其中任一子结构被显式传入，就重建子树
            any_provided = any(
                x is not None for x in [fields_data, target_sheets_data,
                                        sheet_lineages_data, field_lineages_data]
            )
            if any_provided:
                self._rebuild_children(
                    instance,
                    target_sheets_data or [],
                    fields_data or [],
                    sheet_lineages_data or [],
                    field_lineages_data or [],
                )
        return instance


class TaskSheetResultSerializer(serializers.ModelSerializer):
    """任务 Sheet 结果序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = TaskSheetResult
        fields = [
            'id', 'sheet_name', 'target_sheet',
            'status', 'status_display',
            'total_rows', 'success_rows', 'error_rows', 'progress',
            'started_at', 'completed_at', 'duration_ms',
            'error_message', 'execution_order',
        ]

    def get_progress(self, obj):
        if obj.total_rows == 0:
            return 0 if obj.status != TaskSheetResult.Status.COMPLETED else 100
        return round(obj.success_rows / obj.total_rows * 100, 2)


class ProcessingTaskSerializer(serializers.ModelSerializer):
    """处理任务序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    mapping_name = serializers.CharField(source='mapping.name', read_only=True)
    progress = serializers.ReadOnlyField()
    sheet_results = TaskSheetResultSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessingTask
        fields = [
            'id', 'name', 'mapping', 'mapping_name',
            'status', 'status_display',
            'started_at', 'completed_at',
            'total_rows', 'processed_rows', 'success_rows', 'error_rows',
            'progress', 'result_file', 'error_message',
            'sheet_results',
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
