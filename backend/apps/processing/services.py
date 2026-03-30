"""
数据处理服务
Excel parsing and data processing service
"""
import io
import logging
import re
from itertools import product

from django.core.files.base import ContentFile
from django.utils import timezone
from openpyxl import load_workbook, Workbook
from .models import DataMapping, ProcessingTask

logger = logging.getLogger('apps')

# 预编译正则
_FIELD_PATTERN = re.compile(r'\{([^}]+)\}')
_ALLOWED_EXPR_CHARS = frozenset('0123456789.+-*/() ')


class ExcelService:
    """Excel 文件处理服务"""
    
    @staticmethod
    def _read_file_to_bytes(file_obj):
        """从存储后端读取文件到 BytesIO（兼容本地和 S3 存储）"""
        file_field = file_obj.file
        file_field.open('rb')
        try:
            content = file_field.read()
        finally:
            file_field.close()
        return io.BytesIO(content)

    @staticmethod
    def parse_file_fields(file_obj):
        """
        解析 Excel 文件，获取所有 Sheet 及其字段
        返回格式: [{'sheet_name': 'Sheet1', 'fields': [{'name': 'col1', 'index': 0}, ...]}]
        """
        file_bytes = ExcelService._read_file_to_bytes(file_obj)
        wb = load_workbook(file_bytes, read_only=True, data_only=True)
        
        try:
            result = []
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                fields = []
                
                first_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
                if first_row:
                    for index, cell_value in enumerate(first_row):
                        if cell_value is not None:
                            fields.append({'name': str(cell_value), 'index': index})
                
                result.append({'sheet_name': sheet_name, 'fields': fields})
            
            return result
        finally:
            wb.close()
    
    @staticmethod
    def get_sheet_data(file_obj, sheet_name=None):
        """获取 Sheet 的所有数据"""
        file_bytes = ExcelService._read_file_to_bytes(file_obj)
        wb = load_workbook(file_bytes, read_only=True, data_only=True)
        
        try:
            ws = wb[sheet_name] if sheet_name else wb.active
            rows = list(ws.iter_rows(values_only=True))
            
            if not rows:
                return {'headers': [], 'rows': []}
            
            headers = [str(cell) if cell else '' for cell in rows[0]]
            data_rows = [list(row) for row in rows[1:]]
            return {'headers': headers, 'rows': data_rows}
        finally:
            wb.close()

    @staticmethod
    def read_all_sheets(file_obj):
        """读取文件所有 Sheet 数据，返回 {sheet_name: {headers, rows}}"""
        file_bytes = ExcelService._read_file_to_bytes(file_obj)
        wb = load_workbook(file_bytes, read_only=True, data_only=True)
        
        try:
            sheets = {}
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                rows = list(ws.iter_rows(values_only=True))
                if rows:
                    headers = [str(cell) if cell else '' for cell in rows[0]]
                    data_rows = [list(row) for row in rows[1:]]
                    sheets[sheet_name] = {'headers': headers, 'rows': data_rows}
            return sheets
        finally:
            wb.close()


class DataProcessingService:
    """数据处理服务"""
    
    PROGRESS_SAVE_INTERVAL = 100
    
    @staticmethod
    def execute_task(task: ProcessingTask):
        """执行数据处理任务"""
        try:
            task.status = 'running'
            task.started_at = timezone.now()
            task.save(update_fields=['status', 'started_at'])
            
            mapping = task.mapping
            
            # 读取源文件数据
            source_data = ExcelService.get_sheet_data(
                mapping.source_file, mapping.source_sheet or None
            )
            
            # 读取对照文件所有 Sheets 数据
            reference_sheets = {}
            if mapping.reference_file:
                reference_sheets = ExcelService.read_all_sheets(mapping.reference_file)
            
            # 获取字段映射，预构建对照表索引
            field_mappings = list(mapping.fields.all().order_by('sort_order'))
            ref_indexes = DataProcessingService._build_reference_indexes(
                field_mappings, reference_sheets
            )
            
            task.total_rows = len(source_data['rows'])
            task.save(update_fields=['total_rows'])
            
            target_headers = [fm.target_field for fm in field_mappings]
            target_rows = []
            
            for row_idx, source_row in enumerate(source_data['rows']):
                try:
                    result_rows = DataProcessingService._process_row(
                        source_row, source_data['headers'],
                        reference_sheets, field_mappings, ref_indexes
                    )
                    target_rows.extend(result_rows)
                    task.success_rows += 1
                except Exception as e:
                    task.error_rows += 1
                    logger.debug(f"处理第{row_idx+1}行失败: {e}")
                
                task.processed_rows = row_idx + 1
                if row_idx % DataProcessingService.PROGRESS_SAVE_INTERVAL == 0:
                    task.save(update_fields=['processed_rows', 'success_rows', 'error_rows'])
            
            result_file = DataProcessingService._create_result_file(
                target_headers, target_rows, task.name
            )
            
            task.result_file.save(
                f"{task.name}_{timezone.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                result_file
            )
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save(update_fields=[
                'status', 'completed_at', 'processed_rows',
                'success_rows', 'error_rows', 'result_file'
            ])
            return True
            
        except Exception as e:
            logger.exception(f"任务执行失败: task_id={task.id}")
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'error_message', 'completed_at'])
            return False
    
    @staticmethod
    def _build_reference_indexes(field_mappings, reference_sheets):
        """为 lookup 类型字段预构建对照表索引，避免每行重复遍历"""
        indexes = {}
        
        for fm in field_mappings:
            if fm.field_type not in ['lookup', 'source_ref_target']:
                continue
            if not fm.reference_sheet or fm.reference_sheet not in reference_sheets:
                continue
            
            cache_key = (fm.reference_sheet, fm.reference_name_column, fm.reference_code_column)
            if cache_key in indexes:
                continue
            
            ref_data = reference_sheets[fm.reference_sheet]
            headers = ref_data.get('headers', [])
            rows = ref_data.get('rows', [])
            
            name_col_idx = -1
            code_col_idx = -1
            for idx, header in enumerate(headers):
                if header == fm.reference_name_column:
                    name_col_idx = idx
                if header == fm.reference_code_column:
                    code_col_idx = idx
            
            if name_col_idx < 0 or code_col_idx < 0:
                continue
            
            index = {}
            for row in rows:
                if name_col_idx < len(row) and row[name_col_idx] is not None:
                    key = str(row[name_col_idx]).strip()
                    if code_col_idx < len(row):
                        index.setdefault(key, []).append(row[code_col_idx])
            
            indexes[cache_key] = index
        
        return indexes
    
    @staticmethod
    def _process_row(source_row, source_headers, reference_sheets, field_mappings, ref_indexes=None):
        """处理单行数据，可能返回多行结果"""
        source_dict = {
            header: source_row[idx]
            for idx, header in enumerate(source_headers)
            if idx < len(source_row)
        }
        
        field_values = []
        field_is_list = []
        
        for fm in field_mappings:
            value = None
            is_list = False
            
            if fm.field_type in ['direct', 'source_to_target']:
                if fm.source_field and fm.source_field in source_dict:
                    value = source_dict[fm.source_field]
                elif 0 <= fm.source_field_index < len(source_row):
                    value = source_row[fm.source_field_index]
            
            elif fm.field_type in ['lookup', 'source_ref_target']:
                lookup_key = None
                if fm.source_field and fm.source_field in source_dict:
                    lookup_key = source_dict[fm.source_field]
                elif 0 <= fm.source_field_index < len(source_row):
                    lookup_key = source_row[fm.source_field_index]
                
                if lookup_key is not None and fm.reference_sheet:
                    cache_key = (fm.reference_sheet, fm.reference_name_column, fm.reference_code_column)
                    
                    if ref_indexes and cache_key in ref_indexes:
                        matched = ref_indexes[cache_key].get(str(lookup_key).strip(), [])
                    elif fm.reference_sheet in reference_sheets:
                        matched = DataProcessingService._lookup_reference_v2(
                            lookup_key, reference_sheets[fm.reference_sheet],
                            fm.reference_name_column, fm.reference_code_column
                        )
                    else:
                        matched = []
                    
                    if len(matched) > 1:
                        value = matched
                        is_list = True
                    else:
                        value = matched[0] if matched else lookup_key
                else:
                    value = lookup_key
            
            elif fm.field_type == 'computed':
                if fm.compute_expression:
                    value = DataProcessingService._evaluate_expression(
                        fm.compute_expression, source_dict
                    )
            
            elif fm.field_type == 'default':
                value = fm.default_value
            
            elif fm.field_type == 'ref_to_target':
                if fm.reference_sheet and fm.reference_sheet in reference_sheets:
                    ref_data = reference_sheets[fm.reference_sheet]
                    ref_idx = fm.reference_field_index
                    if ref_data['rows'] and 0 <= ref_idx < len(ref_data['rows'][0]):
                        value = ref_data['rows'][0][ref_idx]
            
            if fm.transform_rule:
                if is_list:
                    value = [DataProcessingService._apply_transform(v, fm.transform_rule) for v in value]
                else:
                    value = DataProcessingService._apply_transform(value, fm.transform_rule)
            
            field_values.append(value)
            field_is_list.append(is_list)
        
        if not any(field_is_list):
            return [field_values]
        
        expanded = [
            val if field_is_list[i] else [val]
            for i, val in enumerate(field_values)
        ]
        return [list(combo) for combo in product(*expanded)]
    
    @staticmethod
    def _lookup_reference(source_value, reference_data, lookup_col, result_col):
        """在对照表中查找匹配值（旧版）"""
        if not source_value:
            return source_value
        for row in reference_data['rows']:
            if lookup_col < len(row) and row[lookup_col] == source_value:
                if result_col < len(row):
                    return row[result_col]
        return source_value
    
    @staticmethod
    def _lookup_reference_v2(lookup_key, reference_data, name_column, code_column):
        """在对照表中查找所有匹配值（新版）"""
        if lookup_key is None:
            return [lookup_key]
        
        headers = reference_data.get('headers', [])
        rows = reference_data.get('rows', [])
        
        name_col_idx = -1
        code_col_idx = -1
        for idx, header in enumerate(headers):
            if header == name_column:
                name_col_idx = idx
            if header == code_column:
                code_col_idx = idx
        
        if name_col_idx < 0 or code_col_idx < 0:
            return [lookup_key]
        
        lookup_str = str(lookup_key).strip()
        matched_values = []
        for row in rows:
            if name_col_idx < len(row):
                cell_value = row[name_col_idx]
                if cell_value is not None and str(cell_value).strip() == lookup_str:
                    if code_col_idx < len(row):
                        matched_values.append(row[code_col_idx])
        
        return matched_values if matched_values else [lookup_key]
    
    @staticmethod
    def _apply_transform(value, rule):
        """应用数据转换规则"""
        if not rule or value is None:
            return value
        
        rule_type = rule.get('type')
        str_value = str(value)
        
        if rule_type == 'uppercase':
            return str_value.upper()
        elif rule_type == 'lowercase':
            return str_value.lower()
        elif rule_type == 'prefix':
            return f"{rule.get('value', '')}{value}"
        elif rule_type == 'suffix':
            return f"{value}{rule.get('value', '')}"
        elif rule_type == 'replace':
            return str_value.replace(rule.get('old', ''), rule.get('new', ''))
        return value
    
    @staticmethod
    def _evaluate_expression(expression, source_dict):
        """计算表达式，支持 {字段名} 引用"""
        if not expression:
            return None
        
        def replace_field(match):
            field_name = match.group(1)
            value = source_dict.get(field_name)
            if value is None:
                return '0'
            if isinstance(value, (int, float)):
                return str(value)
            try:
                return str(float(value))
            except (ValueError, TypeError):
                return '0'
        
        result_expr = _FIELD_PATTERN.sub(replace_field, expression)
        
        try:
            if not all(c in _ALLOWED_EXPR_CHARS for c in result_expr):
                return None
            result = eval(result_expr)
            if isinstance(result, float):
                return int(result) if result == int(result) else round(result, 6)
            return result
        except Exception:
            return None
    
    @staticmethod
    def _create_result_file(headers, rows, name):
        """创建结果 Excel 文件"""
        wb = Workbook()
        ws = wb.active
        ws.title = "处理结果"
        
        ws.append(headers)
        for row in rows:
            ws.append(row)
        
        output = io.BytesIO()
        wb.save(output)
        wb.close()
        output.seek(0)
        return ContentFile(output.read())
