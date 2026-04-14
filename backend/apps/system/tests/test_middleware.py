"""
OperationLogMiddleware 单元测试
Unit tests for OperationLogMiddleware slow query warning
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from unittest.mock import patch, MagicMock

import pytest

from apps.system.middleware import OperationLogMiddleware, SLOW_QUERY_THRESHOLD_MS


def _make_request(factory_method='GET', path='/api/files/', user=None):
    """Create a mock request object."""
    request = MagicMock()
    request.method = factory_method
    request.path = path
    request.META = {'HTTP_USER_AGENT': 'test-agent', 'REMOTE_ADDR': '127.0.0.1'}
    request.content_type = 'application/json'
    request.body = b'{}'
    request.GET = MagicMock()
    request.GET.dict.return_value = {}
    request.POST = MagicMock()
    request.POST.dict.return_value = {}
    if user is None:
        request.user = MagicMock()
        request.user.is_authenticated = False
    else:
        request.user = user
    return request


class TestSlowQueryWarning:
    """测试 GET 请求慢查询告警"""

    def test_logs_warning_when_get_exceeds_threshold(self):
        """GET 请求响应时间 > 3s 时应记录慢查询告警"""
        request = _make_request('GET', '/api/files/')
        response = MagicMock(status_code=200)
        middleware = OperationLogMiddleware(lambda r: response)

        with patch('apps.system.middleware.time.monotonic', side_effect=[0.0, 4.0]):
            with patch('apps.system.middleware.logger') as mock_logger:
                middleware(request)
                mock_logger.warning.assert_called_once_with(
                    "慢查询告警",
                    extra={
                        'path': '/api/files/',
                        'method': 'GET',
                        'duration_ms': 4000,
                        'user_id': None,
                    },
                )

    def test_no_warning_when_get_is_fast(self):
        """GET 请求响应时间 <= 3s 时不应记录慢查询告警"""
        request = _make_request('GET', '/api/files/')
        response = MagicMock(status_code=200)
        middleware = OperationLogMiddleware(lambda r: response)

        with patch('apps.system.middleware.time.monotonic', side_effect=[0.0, 2.0]):
            with patch('apps.system.middleware.logger') as mock_logger:
                middleware(request)
                mock_logger.warning.assert_not_called()

    def test_no_warning_when_get_at_exact_threshold(self):
        """GET 请求响应时间恰好 = 3s 时不应记录告警（需 > 3s）"""
        request = _make_request('GET', '/api/files/')
        response = MagicMock(status_code=200)
        middleware = OperationLogMiddleware(lambda r: response)

        with patch('apps.system.middleware.time.monotonic', side_effect=[0.0, 3.0]):
            with patch('apps.system.middleware.logger') as mock_logger:
                middleware(request)
                mock_logger.warning.assert_not_called()

    def test_no_warning_for_slow_post_request(self):
        """POST 请求即使超过 3s 也不应触发慢查询告警（仅 GET）"""
        request = _make_request('POST', '/api/files/')
        request.user.is_authenticated = False
        response = MagicMock(status_code=200)
        middleware = OperationLogMiddleware(lambda r: response)

        with patch('apps.system.middleware.time.monotonic', side_effect=[0.0, 5.0]):
            with patch('apps.system.middleware.logger') as mock_logger:
                middleware(request)
                mock_logger.warning.assert_not_called()

    def test_slow_query_includes_authenticated_user_id(self):
        """慢查询告警应包含已认证用户的 user_id"""
        mock_user = MagicMock()
        mock_user.is_authenticated = True
        mock_user.id = 42
        request = _make_request('GET', '/api/processing/', user=mock_user)

        response = MagicMock(status_code=200)
        middleware = OperationLogMiddleware(lambda r: response)

        with patch('apps.system.middleware.time.monotonic', side_effect=[0.0, 5.0]):
            with patch('apps.system.middleware.logger') as mock_logger:
                middleware(request)
                mock_logger.warning.assert_called_once_with(
                    "慢查询告警",
                    extra={
                        'path': '/api/processing/',
                        'method': 'GET',
                        'duration_ms': 5000,
                        'user_id': 42,
                    },
                )

    def test_threshold_constant_is_3000(self):
        """慢查询阈值应为 3000 毫秒"""
        assert SLOW_QUERY_THRESHOLD_MS == 3000


class TestTimingUsesMonotonic:
    """测试中间件使用 time.monotonic 计时"""

    def test_uses_monotonic_for_timing(self):
        """中间件应使用 time.monotonic() 而非 time.time()"""
        request = _make_request('GET', '/api/files/')
        response = MagicMock(status_code=200)
        middleware = OperationLogMiddleware(lambda r: response)

        with patch('apps.system.middleware.time.monotonic', side_effect=[0.0, 1.0]) as mock_monotonic:
            with patch('apps.system.middleware.time.time') as mock_time:
                middleware(request)
                assert mock_monotonic.call_count == 2
                mock_time.assert_not_called()
