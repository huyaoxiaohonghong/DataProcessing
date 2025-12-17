"""
数据处理服务
Excel parsing and data processing service
"""
import io
import os
from datetime import datetime
from django.core.files.base import ContentFile
from openpyxl import load_workbook, Workbook
from .models import DataMapping, ProcessingTask


class ExcelService:
    """Excel 文件处理服务"""
    
    @staticmethod
    def parse_file_fields(file_obj):
        """
        解析 Excel 文件，获取所有 Sheet 及其字段
        返回格式: [{'sheet_name': 'Sheet1', 'fields': [{'name': 'col1', 'index': 0}, ...]}]
        """
        try:
            file_path = file_obj.file.path
            wb = load_workbook(file_path, read_only=True, data_only=True)
            
            result = []
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                fields = []
                
                # 读取第一行作为字段名
                first_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
                if first_row:
                    for index, cell_value in enumerate(first_row):
                        if cell_value is not None:
                            fields.append({
                                'name': str(cell_value),
                                'index': index
                            })
                
                result.append({
                    'sheet_name': sheet_name,
                    'fields': fields
                })
            
            wb.close()
            return result
            
        except Exception as e:
            raise Exception(f"解析文件失败: {str(e)}")
    
    @staticmethod
    def get_sheet_data(file_obj, sheet_name=None):
        """
        获取 Sheet 的所有数据
        返回格式: {'headers': [...], 'rows': [[...], ...]}
        """
        try:
            file_path = file_obj.file.path
            wb = load_workbook(file_path, read_only=True, data_only=True)
            
            # 如果没有指定 sheet，使用第一个
            if sheet_name:
                ws = wb[sheet_name]
            else:
                ws = wb.active
            
            rows = list(ws.iter_rows(values_only=True))
            wb.close()
            
            if not rows:
                return {'headers': [], 'rows': []}
            
            headers = [str(cell) if cell else '' for cell in rows[0]]
            data_rows = [[cell for cell in row] for row in rows[1:]]
            
            return {
                'headers': headers,
                'rows': data_rows
            }
            
        except Exception as e:
            raise Exception(f"读取数据失败: {str(e)}")


class DataProcessingService:
    """数据处理服务"""
    
    @staticmethod
    def execute_task(task: ProcessingTask):
        """执行数据处理任务"""
        try:
            task.status = 'running'
            task.started_at = datetime.now()
            task.save()
            
            mapping = task.mapping
            
            # 读取源文件数据
            source_data = ExcelService.get_sheet_data(
                mapping.source_file, 
                mapping.source_sheet or None
            )
            
            # 读取对照文件所有Sheets数据（如果有）
            # 格式: {'Sheet名': {'headers': [...], 'rows': [...]}, ...}
            reference_sheets = {}
            if mapping.reference_file:
                file_path = mapping.reference_file.file.path
                wb = load_workbook(file_path, read_only=True, data_only=True)
                for sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    rows = list(ws.iter_rows(values_only=True))
                    if rows:
                        headers = [str(cell) if cell else '' for cell in rows[0]]
                        data_rows = [[cell for cell in row] for row in rows[1:]]
                        reference_sheets[sheet_name] = {
                            'headers': headers,
                            'rows': data_rows
                        }
                wb.close()
            
            # 获取字段映射
            field_mappings = list(mapping.fields.all().order_by('sort_order'))
            
            task.total_rows = len(source_data['rows'])
            task.save()
            
            # 生成目标数据
            target_headers = [fm.target_field for fm in field_mappings]
            target_rows = []
            
            for row_idx, source_row in enumerate(source_data['rows']):
                try:
                    # _process_row 现在返回行列表（一行源数据可能产生多行目标数据）
                    result_rows = DataProcessingService._process_row(
                        source_row, 
                        source_data['headers'],
                        reference_sheets,
                        field_mappings
                    )
                    target_rows.extend(result_rows)
                    task.success_rows += 1
                except Exception as e:
                    task.error_rows += 1
                
                task.processed_rows = row_idx + 1
                if row_idx % 100 == 0:
                    task.save()
            
            # 生成结果文件
            result_file = DataProcessingService._create_result_file(
                target_headers, 
                target_rows,
                task.name
            )
            
            task.result_file.save(
                f"{task.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx",
                result_file
            )
            task.status = 'completed'
            task.completed_at = datetime.now()
            task.save()
            
            return True
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.completed_at = datetime.now()
            task.save()
            return False
    
    @staticmethod
    def _process_row(source_row, source_headers, reference_sheets, field_mappings):
        """处理单行数据，可能返回多行结果
        
        Args:
            source_row: 源数据行
            source_headers: 源数据表头
            reference_sheets: 对照表字典 {'Sheet名': {'headers': [...], 'rows': [...]}}
            field_mappings: 字段映射列表
            
        Returns:
            目标数据行列表（一行源数据可能产生多行目标数据）
        """
        from itertools import product
        
        # 构建源数据字典，方便按字段名查找
        source_dict = {}
        for idx, header in enumerate(source_headers):
            if idx < len(source_row):
                source_dict[header] = source_row[idx]
        
        # 收集每个字段的值（可能是列表）
        field_values = []
        field_is_list = []  # 记录哪些字段是列表（需要展开）
        
        for fm in field_mappings:
            value = None
            is_list = False
            
            # 1. 直接映射 (direct) 或旧的 source_to_target
            if fm.field_type in ['direct', 'source_to_target']:
                if fm.source_field and fm.source_field in source_dict:
                    value = source_dict[fm.source_field]
                elif fm.source_field_index >= 0 and fm.source_field_index < len(source_row):
                    value = source_row[fm.source_field_index]
            
            # 2. 对照表转换 (lookup) 或旧的 source_ref_target
            elif fm.field_type in ['lookup', 'source_ref_target']:
                # 先从源数据获取查找键
                lookup_key = None
                if fm.source_field and fm.source_field in source_dict:
                    lookup_key = source_dict[fm.source_field]
                elif fm.source_field_index >= 0 and fm.source_field_index < len(source_row):
                    lookup_key = source_row[fm.source_field_index]
                
                # 在对照表中查找（返回列表）
                if lookup_key is not None and fm.reference_sheet and fm.reference_sheet in reference_sheets:
                    matched_values = DataProcessingService._lookup_reference_v2(
                        lookup_key,
                        reference_sheets[fm.reference_sheet],
                        fm.reference_name_column,
                        fm.reference_code_column
                    )
                    # matched_values 是一个列表
                    if len(matched_values) > 1:
                        value = matched_values
                        is_list = True
                    else:
                        value = matched_values[0] if matched_values else lookup_key
                else:
                    value = lookup_key
            
            # 3. 计算字段 (computed)
            elif fm.field_type == 'computed':
                if fm.compute_expression:
                    value = DataProcessingService._evaluate_expression(
                        fm.compute_expression,
                        source_dict
                    )
            
            # 4. 默认值 (default)
            elif fm.field_type == 'default':
                value = fm.default_value
            
            # 5. 旧的 ref_to_target (直接从对照表获取，兼容旧数据)
            elif fm.field_type == 'ref_to_target':
                if fm.reference_sheet and fm.reference_sheet in reference_sheets:
                    ref_data = reference_sheets[fm.reference_sheet]
                    ref_idx = fm.reference_field_index
                    if ref_data['rows'] and ref_idx >= 0 and ref_idx < len(ref_data['rows'][0]):
                        value = ref_data['rows'][0][ref_idx]
            
            # 应用转换规则
            if fm.transform_rule and not is_list:
                value = DataProcessingService._apply_transform(value, fm.transform_rule)
            elif fm.transform_rule and is_list:
                value = [DataProcessingService._apply_transform(v, fm.transform_rule) for v in value]
            
            field_values.append(value)
            field_is_list.append(is_list)
        
        # 如果没有列表字段，直接返回单行结果
        if not any(field_is_list):
            return [field_values]
        
        # 有列表字段，需要展开为多行
        # 将非列表值包装为单元素列表，以便使用笛卡尔积
        expanded_values = []
        for i, val in enumerate(field_values):
            if field_is_list[i]:
                expanded_values.append(val)
            else:
                expanded_values.append([val])
        
        # 使用笛卡尔积生成所有组合
        result_rows = [list(combo) for combo in product(*expanded_values)]
        
        return result_rows
    
    @staticmethod
    def _lookup_reference(source_value, reference_data, lookup_col, result_col):
        """在对照表中查找匹配值（旧版，使用列索引）"""
        if not source_value:
            return source_value
        
        for row in reference_data['rows']:
            if lookup_col < len(row) and row[lookup_col] == source_value:
                if result_col < len(row):
                    return row[result_col]
        
        return source_value
    
    @staticmethod
    def _lookup_reference_v2(lookup_key, reference_data, name_column, code_column):
        """在对照表中查找所有匹配值（新版，使用列名）
        
        Args:
            lookup_key: 查找键值（源数据中的值）
            reference_data: 对照表数据 {'headers': [...], 'rows': [...]}
            name_column: 名称列（用于匹配的列名）
            code_column: 编码列（返回结果的列名）
        
        Returns:
            匹配到的编码值列表，如果未找到则返回包含原值的列表
        """
        if lookup_key is None:
            return [lookup_key]
        
        headers = reference_data.get('headers', [])
        rows = reference_data.get('rows', [])
        
        # 查找列索引
        name_col_idx = -1
        code_col_idx = -1
        
        for idx, header in enumerate(headers):
            if header == name_column:
                name_col_idx = idx
            if header == code_column:
                code_col_idx = idx
        
        if name_col_idx < 0 or code_col_idx < 0:
            return [lookup_key]  # 找不到列，返回包含原值的列表
        
        # 在数据中查找所有匹配行
        lookup_str = str(lookup_key).strip()
        matched_values = []
        
        for row in rows:
            if name_col_idx < len(row):
                cell_value = row[name_col_idx]
                if cell_value is not None and str(cell_value).strip() == lookup_str:
                    if code_col_idx < len(row):
                        matched_values.append(row[code_col_idx])
        
        # 如果找到匹配，返回所有匹配值；否则返回原值
        return matched_values if matched_values else [lookup_key]
    
    @staticmethod
    def _apply_transform(value, rule):
        """应用数据转换规则"""
        if not rule:
            return value
        
        rule_type = rule.get('type')
        
        if rule_type == 'uppercase':
            return str(value).upper() if value else value
        elif rule_type == 'lowercase':
            return str(value).lower() if value else value
        elif rule_type == 'prefix':
            prefix = rule.get('value', '')
            return f"{prefix}{value}" if value else value
        elif rule_type == 'suffix':
            suffix = rule.get('value', '')
            return f"{value}{suffix}" if value else value
        elif rule_type == 'replace':
            old_val = rule.get('old', '')
            new_val = rule.get('new', '')
            return str(value).replace(old_val, new_val) if value else value
        
        return value
    
    @staticmethod
    def _evaluate_expression(expression, source_dict):
        """计算表达式
        
        支持的格式: {字段名} 会被替换为对应的值
        例如: {使用月限} / 12
        
        Args:
            expression: 表达式字符串
            source_dict: 源数据字典 {字段名: 值}
        
        Returns:
            计算结果
        """
        import re
        
        if not expression:
            return None
        
        # 替换表达式中的字段引用
        result_expr = expression
        field_pattern = r'\{([^}]+)\}'
        
        def replace_field(match):
            field_name = match.group(1)
            value = source_dict.get(field_name)
            if value is None:
                return '0'
            # 数值类型直接返回
            if isinstance(value, (int, float)):
                return str(value)
            # 尝试转换为数值
            try:
                return str(float(value))
            except (ValueError, TypeError):
                return '0'
        
        result_expr = re.sub(field_pattern, replace_field, result_expr)
        
        # 安全地计算表达式（只允许数学运算）
        try:
            # 只允许数字、运算符和括号
            allowed_chars = set('0123456789.+-*/() ')
            if not all(c in allowed_chars for c in result_expr):
                return None
            
            # 计算表达式
            result = eval(result_expr)
            
            # 如果结果是浮点数，保留合理的小数位
            if isinstance(result, float):
                if result == int(result):
                    return int(result)
                return round(result, 6)
            return result
        except Exception:
            return None
    
    @staticmethod
    def _create_result_file(headers, rows, name):
        """创建结果 Excel 文件"""
        wb = Workbook()
        ws = wb.active
        ws.title = "处理结果"
        
        # 写入表头
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # 写入数据
        for row_idx, row in enumerate(rows, 2):
            for col_idx, value in enumerate(row, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)
        
        # 保存到内存
        output = io.BytesIO()
        wb.save(output)
        wb.close()
        output.seek(0)
        
        return ContentFile(output.read())
