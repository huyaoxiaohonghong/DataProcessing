"""
速率限制器
Rate Limiter based on Redis sliding window algorithm
"""
import time
import uuid
import logging

from django_redis import get_redis_connection

logger = logging.getLogger('apps')


class RateLimiter:
    """基于 Redis 滑动窗口的速率限制器"""

    # IP 封锁相关常量
    BLOCK_THRESHOLD = 15       # 封锁阈值：30 分钟内失败次数
    BLOCK_WINDOW = 1800        # 失败记录窗口 & 封锁时长（秒）

    @staticmethod
    def get_client_ip(request) -> str:
        """
        从请求中提取客户端真实 IP（支持 X-Forwarded-For）
        :param request: Django HttpRequest
        :return: 客户端 IP 地址
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # 取第一个 IP（最接近客户端的）
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    @staticmethod
    def is_rate_limited(key: str, max_requests: int, window_seconds: int) -> bool:
        """
        检查是否超过速率限制（滑动窗口算法，使用 Redis Sorted Set）
        :param key: 限制键 (如 "rate:captcha:{ip}")
        :param max_requests: 窗口内最大请求数
        :param window_seconds: 窗口大小 (秒)
        :return: True 表示已超限
        """
        try:
            conn = get_redis_connection("default")
            now = time.time()
            window_start = now - window_seconds
            member = f"{now}:{uuid.uuid4().hex[:8]}"

            pipe = conn.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)   # 清除过期记录
            pipe.zadd(key, {member: now})                  # 添加当前请求
            pipe.zcard(key)                                # 计算窗口内请求数
            pipe.expire(key, window_seconds)               # 设置键过期
            results = pipe.execute()

            count = results[2]
            return count > max_requests
        except Exception as e:
            logger.warning(f"Rate limiter error (degraded to allow): {e}")
            return False

    @staticmethod
    def record_login_failure(ip: str) -> None:
        """
        记录登录失败到 login:fail:{ip} 键（Sorted Set，TTL 1800s）
        :param ip: 客户端 IP 地址
        """
        try:
            conn = get_redis_connection("default")
            key = f"login:fail:{ip}"
            now = time.time()
            member = f"{now}:{uuid.uuid4().hex[:8]}"

            pipe = conn.pipeline()
            pipe.zadd(key, {member: now})
            pipe.expire(key, RateLimiter.BLOCK_WINDOW)
            pipe.execute()
        except Exception as e:
            logger.warning(f"Record login failure error: {e}")

    @staticmethod
    def is_ip_blocked(ip: str) -> bool:
        """
        检查 IP 是否被封锁。
        先检查 login:block:{ip} 是否存在；
        若不存在，检查 login:fail:{ip} 中 30 分钟内记录是否 ≥ 15 条，
        若达到阈值则设置封锁标记（TTL 1800s）。
        :param ip: 客户端 IP 地址
        :return: True 表示 IP 被封锁
        """
        try:
            conn = get_redis_connection("default")
            block_key = f"login:block:{ip}"
            fail_key = f"login:fail:{ip}"

            # 先检查封锁标记
            if conn.exists(block_key):
                return True

            # 检查失败记录数
            now = time.time()
            window_start = now - RateLimiter.BLOCK_WINDOW
            # 清除过期记录后计数
            conn.zremrangebyscore(fail_key, 0, window_start)
            fail_count = conn.zcard(fail_key)

            if fail_count >= RateLimiter.BLOCK_THRESHOLD:
                # 设置封锁标记
                conn.set(block_key, "1", ex=RateLimiter.BLOCK_WINDOW)
                return True

            return False
        except Exception as e:
            logger.warning(f"IP block check error (degraded to allow): {e}")
            return False
