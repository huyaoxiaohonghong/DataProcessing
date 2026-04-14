"""
共享 pytest fixtures
Shared fixtures for test users, files, mapping configs, and processing tasks.
"""
import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


# ---------------------------------------------------------------------------
# Helper: 生成内存中的 Excel 文件字节
# ---------------------------------------------------------------------------

def make_excel_bytes(sheets: dict[str, list[list]] | None = None) -> bytes:
    """
    创建一个内存 Excel 文件并返回 bytes。

    Parameters
    ----------
    sheets : dict mapping sheet_name -> list of rows (each row is a list).
             If *None*, creates a single sheet with a header row.
    """
    wb = Workbook()
    if sheets is None:
        sheets = {"Sheet1": [["col_a", "col_b", "col_c"]]}

    first = True
    for name, rows in sheets.items():
        ws = wb.active if first else wb.create_sheet(title=name)
        if first:
            ws.title = name
            first = False
        for row in rows:
            ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    wb.close()
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Database access
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _enable_db(db):
    """All tests in backend/tests/ get database access by default."""
    pass


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user(django_user_model):
    """普通测试用户"""
    user = django_user_model.objects.create_user(
        username="testuser",
        password="TestPass123!",
        email="testuser@example.com",
        role="user",
        is_active=True,
    )
    return user


@pytest.fixture
def admin_user(django_user_model):
    """管理员测试用户"""
    user = django_user_model.objects.create_user(
        username="adminuser",
        password="AdminPass123!",
        email="admin@example.com",
        role="admin",
        is_active=True,
    )
    return user


@pytest.fixture
def super_admin_user(django_user_model):
    """超级管理员测试用户"""
    user = django_user_model.objects.create_superuser(
        username="superadmin",
        password="SuperPass123!",
        email="superadmin@example.com",
        role="super_admin",
    )
    return user


# ---------------------------------------------------------------------------
# Authenticated API clients
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    """未认证的 DRF APIClient"""
    return APIClient()


@pytest.fixture
def auth_client(test_user, api_client):
    """以普通用户身份认证的 APIClient (JWT Bearer)"""
    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def admin_client(admin_user):
    """以管理员身份认证的 APIClient (JWT Bearer)"""
    client = APIClient()
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


# ---------------------------------------------------------------------------
# Test files (Django File model instances)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_excel_bytes():
    """带有表头和数据行的 Excel 文件 bytes"""
    return make_excel_bytes(
        {
            "Sheet1": [
                ["资产名称", "资产编码", "使用月限"],
                ["电脑", "PC001", 36],
                ["打印机", "PR001", 60],
            ]
        }
    )


@pytest.fixture
def sample_uploaded_file(sample_excel_bytes):
    """SimpleUploadedFile，可直接用于上传接口测试"""
    return SimpleUploadedFile(
        name="test_upload.xlsx",
        content=sample_excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@pytest.fixture
def test_file(test_user, sample_excel_bytes):
    """已保存到数据库的 File 模型实例"""
    from apps.files.models import File

    uploaded = SimpleUploadedFile(
        name="source.xlsx",
        content=sample_excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    file_obj = File.objects.create(
        name="source.xlsx",
        original_name="source.xlsx",
        file=uploaded,
        file_size=len(sample_excel_bytes),
        file_type="xlsx",
        status="active",
        uploaded_by=test_user,
    )
    return file_obj


@pytest.fixture
def reference_excel_bytes():
    """对照表 Excel 文件 bytes"""
    return make_excel_bytes(
        {
            "对照表": [
                ["资产名称", "科目编码"],
                ["电脑", "1601.01"],
                ["打印机", "1601.02"],
                ["服务器", "1601.03"],
            ]
        }
    )


@pytest.fixture
def reference_file(test_user, reference_excel_bytes):
    """对照表 File 模型实例"""
    from apps.files.models import File

    uploaded = SimpleUploadedFile(
        name="reference.xlsx",
        content=reference_excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    file_obj = File.objects.create(
        name="reference.xlsx",
        original_name="reference.xlsx",
        file=uploaded,
        file_size=len(reference_excel_bytes),
        file_type="xlsx",
        status="active",
        uploaded_by=test_user,
    )
    return file_obj


# ---------------------------------------------------------------------------
# Data mapping configuration
# ---------------------------------------------------------------------------

@pytest.fixture
def test_mapping(test_user, test_file, reference_file):
    """完整的数据映射配置（含 source、reference 文件和字段映射）"""
    from apps.processing.models import DataMapping, MappingField

    mapping = DataMapping.objects.create(
        name="测试配置",
        description="用于单元测试的映射配置",
        source_file=test_file,
        source_sheet="Sheet1",
        reference_file=reference_file,
        reference_sheet="对照表",
        status="active",
        created_by=test_user,
    )

    # direct 映射
    MappingField.objects.create(
        mapping=mapping,
        source_field="资产名称",
        target_field="名称",
        field_type="direct",
        sort_order=0,
    )

    # lookup 映射
    MappingField.objects.create(
        mapping=mapping,
        source_field="资产名称",
        target_field="科目编码",
        field_type="lookup",
        reference_sheet="对照表",
        reference_name_column="资产名称",
        reference_code_column="科目编码",
        sort_order=1,
    )

    # computed 映射
    MappingField.objects.create(
        mapping=mapping,
        target_field="月折旧",
        field_type="computed",
        compute_expression="{使用月限}/12",
        sort_order=2,
    )

    # default 映射
    MappingField.objects.create(
        mapping=mapping,
        target_field="部门",
        field_type="default",
        default_value="IT部",
        sort_order=3,
    )

    return mapping


# ---------------------------------------------------------------------------
# Processing task
# ---------------------------------------------------------------------------

@pytest.fixture
def test_task(test_user, test_mapping):
    """待执行的处理任务"""
    from apps.processing.models import ProcessingTask

    task = ProcessingTask.objects.create(
        name="测试任务",
        mapping=test_mapping,
        status="pending",
        created_by=test_user,
    )
    return task
