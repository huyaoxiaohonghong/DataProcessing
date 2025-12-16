from rest_framework import serializers
from .models import LoginLog, OperationLog, Department, Menu, RolePermission

class LoginLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginLog
        fields = '__all__'

class OperationLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = OperationLog
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'parent', 'parent_name', 'leader', 'phone', 
                  'email', 'sort', 'status', 'remark', 'created_at', 'updated_at', 'children']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_children(self, obj):
        # 仅在获取树形结构时使用
        if self.context.get('tree'):
            children = obj.children.all()
            return DepartmentSerializer(children, many=True, context=self.context).data
        return []


class DepartmentSimpleSerializer(serializers.ModelSerializer):
    """简单部门序列化器（用于下拉选择）"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'code']


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    menu_type_display = serializers.CharField(source='get_menu_type_display', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Menu
        fields = ['id', 'name', 'parent', 'parent_name', 'path', 'component', 'icon',
                  'menu_type', 'menu_type_display', 'permission', 'sort', 'status', 
                  'visible', 'cache', 'remark', 'created_at', 'updated_at', 'children']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_children(self, obj):
        if self.context.get('tree'):
            children = obj.children.all().order_by('sort')
            return MenuSerializer(children, many=True, context=self.context).data
        return []


class MenuSimpleSerializer(serializers.ModelSerializer):
    """简单菜单序列化器（用于下拉选择）"""
    class Meta:
        model = Menu
        fields = ['id', 'name', 'menu_type']


class RolePermissionSerializer(serializers.ModelSerializer):
    """角色权限序列化器"""
    menu_name = serializers.CharField(source='menu.name', read_only=True)
    data_scope_display = serializers.CharField(source='get_data_scope_display', read_only=True)
    department_ids = serializers.PrimaryKeyRelatedField(
        source='departments', 
        many=True, 
        queryset=Department.objects.all(),
        required=False
    )
    
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'menu', 'menu_name', 'data_scope', 'data_scope_display',
                  'department_ids', 'created_at']
        read_only_fields = ['created_at']

