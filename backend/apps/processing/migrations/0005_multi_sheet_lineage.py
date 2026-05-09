"""
多 Sheet 映射 + 血缘 + 任务 Sheet 结果

新增模型：
  - MappingTargetSheet：目标 sheet 配置（一个 mapping 多 sheet）
  - SheetLineage：sheet 之间的血缘关系
  - FieldLineage：字段之间的血缘关系
  - TaskSheetResult：任务中每个 sheet 的独立执行结果

字段变更：
  - MappingField 新增 target_sheet_config / source_target_sheet /
    source_target_field / aggregation
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('processing', '0004_add_celery_task_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='MappingTargetSheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sheet_name', models.CharField(max_length=100, verbose_name='目标Sheet名称')),
                ('display_name', models.CharField(blank=True, max_length=200, verbose_name='展示名称')),
                ('description', models.TextField(blank=True, default='', verbose_name='说明')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('ready', '已就绪'), ('disabled', '已禁用')], default='draft', max_length=20, verbose_name='状态')),
                ('source_sheet', models.CharField(blank=True, default='', max_length=100, verbose_name='源Sheet')),
                ('sort_order', models.IntegerField(default=0, verbose_name='排序')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('mapping', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_sheets', to='processing.datamapping', verbose_name='所属配置')),
            ],
            options={
                'verbose_name': '目标Sheet配置',
                'verbose_name_plural': '目标Sheet配置',
                'db_table': 'mapping_target_sheets',
                'ordering': ['sort_order', 'id'],
                'unique_together': {('mapping', 'sheet_name')},
            },
        ),
        migrations.AddField(
            model_name='mappingfield',
            name='target_sheet_config',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='processing.mappingtargetsheet', verbose_name='所属目标Sheet'),
        ),
        migrations.AddField(
            model_name='mappingfield',
            name='source_target_sheet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referenced_by_fields', to='processing.mappingtargetsheet', verbose_name='引用的目标Sheet'),
        ),
        migrations.AddField(
            model_name='mappingfield',
            name='source_target_field',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='引用的目标Sheet字段'),
        ),
        migrations.AddField(
            model_name='mappingfield',
            name='aggregation',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='聚合方式'),
        ),
        migrations.AlterField(
            model_name='mappingfield',
            name='field_type',
            field=models.CharField(
                choices=[
                    ('direct', '直接映射'), ('lookup', '对照表转换'),
                    ('computed', '计算字段'), ('default', '默认值'),
                    ('cross_sheet_ref', '跨Sheet引用'),
                    ('source_to_target', '源→目标'), ('source_to_ref', '源→对照'),
                    ('ref_to_target', '对照→目标'), ('source_ref_target', '源→对照→目标'),
                ],
                default='direct', max_length=30, verbose_name='映射类型'
            ),
        ),
        migrations.CreateModel(
            name='SheetLineage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation_type', models.CharField(choices=[('derived', '派生'), ('aggregated', '聚合'), ('joined', '关联'), ('reference', '引用')], default='derived', max_length=20, verbose_name='关系类型')),
                ('join_keys', models.JSONField(blank=True, null=True, verbose_name='关联键配置')),
                ('description', models.CharField(blank=True, default='', max_length=500, verbose_name='关系描述')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mapping', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sheet_lineages', to='processing.datamapping', verbose_name='所属配置')),
                ('upstream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='downstream_lineages', to='processing.mappingtargetsheet', verbose_name='上游Sheet')),
                ('downstream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upstream_lineages', to='processing.mappingtargetsheet', verbose_name='下游Sheet')),
            ],
            options={
                'verbose_name': 'Sheet血缘',
                'verbose_name_plural': 'Sheet血缘',
                'db_table': 'sheet_lineages',
                'ordering': ['id'],
                'unique_together': {('upstream', 'downstream', 'relation_type')},
            },
        ),
        migrations.CreateModel(
            name='FieldLineage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upstream_field', models.CharField(max_length=200, verbose_name='上游字段')),
                ('downstream_field', models.CharField(max_length=200, verbose_name='下游字段')),
                ('transform', models.CharField(default='direct', max_length=30, verbose_name='传播方式')),
                ('note', models.CharField(blank=True, default='', max_length=500, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mapping', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='field_lineages', to='processing.datamapping', verbose_name='所属配置')),
                ('upstream_sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='downstream_field_lineages', to='processing.mappingtargetsheet', verbose_name='上游Sheet')),
                ('downstream_sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upstream_field_lineages', to='processing.mappingtargetsheet', verbose_name='下游Sheet')),
            ],
            options={
                'verbose_name': '字段血缘',
                'verbose_name_plural': '字段血缘',
                'db_table': 'field_lineages',
                'ordering': ['id'],
                'indexes': [
                    models.Index(fields=['mapping', 'downstream_sheet'], name='field_linea_mapping_down_idx'),
                    models.Index(fields=['mapping', 'upstream_sheet'], name='field_linea_mapping_up_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='TaskSheetResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sheet_name', models.CharField(max_length=100, verbose_name='Sheet名称')),
                ('status', models.CharField(choices=[('pending', '待执行'), ('running', '执行中'), ('completed', '已完成'), ('failed', '失败'), ('skipped', '已跳过')], default='pending', max_length=20, verbose_name='状态')),
                ('total_rows', models.IntegerField(default=0, verbose_name='总行数')),
                ('success_rows', models.IntegerField(default=0, verbose_name='成功行数')),
                ('error_rows', models.IntegerField(default=0, verbose_name='错误行数')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('duration_ms', models.IntegerField(default=0, verbose_name='耗时(毫秒)')),
                ('error_message', models.TextField(blank=True, default='', verbose_name='错误信息')),
                ('execution_order', models.IntegerField(default=0, verbose_name='执行顺序')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sheet_results', to='processing.processingtask', verbose_name='所属任务')),
                ('target_sheet', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_results', to='processing.mappingtargetsheet', verbose_name='目标Sheet配置')),
            ],
            options={
                'verbose_name': '任务Sheet结果',
                'verbose_name_plural': '任务Sheet结果',
                'db_table': 'task_sheet_results',
                'ordering': ['task', 'execution_order'],
                'indexes': [
                    models.Index(fields=['task', 'status'], name='task_sheet_res_task_st_idx'),
                ],
            },
        ),
    ]
