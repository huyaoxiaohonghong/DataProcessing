"""
RateLimiter 单元测试
Unit tests for RateLimiter
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory

from apps.system.rate_limiter import RateLimiter


class TestGetClientIp(TestCase):
    """测试 get_client_ip 方法"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_remote_addr_when_no_forwarded_header(self):
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        self.assertEqual(RateLimiter.get_client_ip(request), '192.168.1.100')

    def test_returns_first_ip_from_x_forwarded_for(self):
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 10.0.0.2, 10.0.0.3'
        self.assertEqual(RateLimiter.get_client_ip(request), '10.0.0.1')

    def test_returns_single_x_forwarded_for_ip(self):
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.50'
        self.assertEqual(RateLimiter.get_client_ip(request), '203.0.113.50')

    def test_strips_whitespace_from_forwarded_ip(self):
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '  10.0.0.1 , 10.0.0.2'
        self.assertEqual(RateLimiter.get_client_ip(request), '10.0.0.1')

    def test_defaults_to_localhost_when_no_remote_addr(self):
        request = self.factory.get('/')
        request.META.pop('REMOTE_ADDR', None)
        self.assertEqual(RateLimiter.get_client_ip(request), '127.0.0.1')


class TestIsRateLimited(TestCase):
    """测试 is_rate_limited 方法"""

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_allows_requests_within_limit(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_pipe = MagicMock()
        mock_conn.pipeline.return_value = mock_pipe
        # zcard returns count within limit
        mock_pipe.execute.return_value = [0, True, 3, True]
        mock_get_conn.return_value = mock_conn

        result = RateLimiter.is_rate_limited("rate:test:1.2.3.4", 10, 60)
        self.assertFalse(result)

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_blocks_requests_exceeding_limit(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_pipe = MagicMock()
        mock_conn.pipeline.return_value = mock_pipe
        # zcard returns count exceeding limit
        mock_pipe.execute.return_value = [0, True, 11, True]
        mock_get_conn.return_value = mock_conn

        result = RateLimiter.is_rate_limited("rate:test:1.2.3.4", 10, 60)
        self.assertTrue(result)

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_allows_requests_at_exact_limit(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_pipe = MagicMock()
        mock_conn.pipeline.return_value = mock_pipe
        # zcard returns count exactly at limit (not exceeded)
        mock_pipe.execute.return_value = [0, True, 10, True]
        mock_get_conn.return_value = mock_conn

        result = RateLimiter.is_rate_limited("rate:test:1.2.3.4", 10, 60)
        self.assertFalse(result)

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_degrades_to_allow_on_redis_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Redis connection failed")

        result = RateLimiter.is_rate_limited("rate:test:1.2.3.4", 10, 60)
        self.assertFalse(result)


class TestRecordLoginFailure(TestCase):
    """测试 record_login_failure 方法"""

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_records_failure_in_sorted_set(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_pipe = MagicMock()
        mock_conn.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [1, True]
        mock_get_conn.return_value = mock_conn

        RateLimiter.record_login_failure("1.2.3.4")

        mock_pipe.zadd.assert_called_once()
        mock_pipe.expire.assert_called_once_with("login:fail:1.2.3.4", 1800)
        mock_pipe.execute.assert_called_once()

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_does_not_raise_on_redis_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Redis connection failed")
        # Should not raise
        RateLimiter.record_login_failure("1.2.3.4")


class TestIsIpBlocked(TestCase):
    """测试 is_ip_blocked 方法"""

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_returns_true_when_block_key_exists(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_conn.exists.return_value = True
        mock_get_conn.return_value = mock_conn

        result = RateLimiter.is_ip_blocked("1.2.3.4")
        self.assertTrue(result)
        mock_conn.exists.assert_called_once_with("login:block:1.2.3.4")

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_returns_false_when_below_threshold(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_conn.exists.return_value = False
        mock_conn.zcard.return_value = 10
        mock_get_conn.return_value = mock_conn

        result = RateLimiter.is_ip_blocked("1.2.3.4")
        self.assertFalse(result)

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_blocks_ip_when_threshold_reached(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_conn.exists.return_value = False
        mock_conn.zcard.return_value = 15
        mock_get_conn.return_value = mock_conn

        result = RateLimiter.is_ip_blocked("1.2.3.4")
        self.assertTrue(result)
        mock_conn.set.assert_called_once_with(
            "login:block:1.2.3.4", "1", ex=1800
        )

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_blocks_ip_when_above_threshold(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_conn.exists.return_value = False
        mock_conn.zcard.return_value = 20
        mock_get_conn.return_value = mock_conn

        result = RateLimiter.is_ip_blocked("1.2.3.4")
        self.assertTrue(result)

    @patch('apps.system.rate_limiter.get_redis_connection')
    def test_degrades_to_allow_on_redis_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Redis connection failed")

        result = RateLimiter.is_ip_blocked("1.2.3.4")
        self.assertFalse(result)
