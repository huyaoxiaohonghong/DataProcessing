"""
Redis 缓存工具类
Cache utilities for data caching with Redis
"""
import logging
from django.core.cache import cache
from functools import wraps
import json
import hashlib

logger = logging.getLogger('apps')


class CacheKeys:
    """缓存键常量"""
    # 用户相关
    USER_INFO = 'user:info:{}'
    USER_LIST = 'users:list:{}'
    USER_ROLES = 'users:roles'
    
    # 部门相关
    DEPARTMENT_LIST = 'departments:list:{}'
    DEPARTMENT_TREE = 'departments:tree'
    DEPARTMENT_SIMPLE = 'departments:simple'
    
    # 菜单相关
    MENU_LIST = 'menus:list:{}'
    MENU_TREE = 'menus:tree'
    MENU_SIMPLE = 'menus:simple'
    MENU_TYPES = 'menus:types'
    
    # 文件相关
    FILE_LIST = 'files:list:{}'
    FILE_STATISTICS = 'files:statistics:{}'
    FILE_CATEGORIES = 'file_categories:list'
    
    # 日志相关
    LOGIN_LOGS = 'logs:login:{}'
    OPERATION_LOGS = 'logs:operation:{}'


class CacheService:
    """缓存服务类"""
    
    # 默认缓存时间（秒）
    DEFAULT_TIMEOUT = 300  # 5分钟
    SHORT_TIMEOUT = 60     # 1分钟
    LONG_TIMEOUT = 3600    # 1小时
    
    @staticmethod
    def get(key: str):
        """获取缓存"""
        try:
            return cache.get(key)
        except Exception as e:
            logger.error(f"Redis 读取失败，降级为无缓存: {e}")
            return None
    
    @staticmethod
    def set(key: str, value, timeout: int = None):
        """设置缓存"""
        if timeout is None:
            timeout = CacheService.DEFAULT_TIMEOUT
        try:
            cache.set(key, value, timeout)
        except Exception as e:
            logger.error(f"Redis 写入失败，降级为无缓存: {e}")
    
    @staticmethod
    def delete(key: str):
        """删除缓存"""
        try:
            cache.delete(key)
        except Exception as e:
            logger.error(f"Redis 删除失败，降级为无缓存: {e}")
    
    @staticmethod
    def delete_pattern(pattern: str):
        """删除匹配模式的缓存"""
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection("default")
            # 获取所有匹配的键
            keys = conn.keys(f'dps:{pattern}')
            if keys:
                conn.delete(*keys)
        except Exception as e:
            logger.warning(f"Delete pattern error: {e}")
    
    @staticmethod
    def clear_user_cache(user_id: int = None):
        """清除用户相关缓存"""
        if user_id:
            CacheService.delete(CacheKeys.USER_INFO.format(user_id))
        CacheService.delete_pattern('users:*')
        CacheService.delete(CacheKeys.USER_ROLES)
    
    @staticmethod
    def clear_department_cache():
        """清除部门相关缓存"""
        CacheService.delete_pattern('departments:*')
        CacheService.delete(CacheKeys.DEPARTMENT_TREE)
        CacheService.delete(CacheKeys.DEPARTMENT_SIMPLE)
    
    @staticmethod
    def clear_menu_cache():
        """清除菜单相关缓存"""
        CacheService.delete_pattern('menus:*')
        CacheService.delete(CacheKeys.MENU_TREE)
        CacheService.delete(CacheKeys.MENU_SIMPLE)
        CacheService.delete(CacheKeys.MENU_TYPES)
    
    @staticmethod
    def clear_file_cache():
        """清除文件相关缓存"""
        CacheService.delete_pattern('files:*')
        CacheService.delete(CacheKeys.FILE_CATEGORIES)
    
    @staticmethod
    def clear_all():
        """清除所有缓存"""
        try:
            cache.clear()
        except Exception as e:
            logger.error(f"Redis 清除全部缓存失败，降级为无缓存: {e}")
    
    @staticmethod
    def generate_cache_key(prefix: str, params: dict = None) -> str:
        """生成缓存键"""
        if params:
            # 对参数进行排序后生成hash
            sorted_params = sorted(params.items())
            params_str = json.dumps(sorted_params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"{prefix}:{params_hash}"
        return prefix


def cache_response(key_prefix: str, timeout: int = 300):
    """
    缓存装饰器 - 用于视图方法
    
    用法:
    @cache_response('users:list', timeout=300)
    def list(self, request):
        ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # 生成缓存键
            params = dict(request.query_params)
            params['user_id'] = request.user.id if request.user.is_authenticated else 0
            cache_key = CacheService.generate_cache_key(key_prefix, params)
            
            # 尝试从缓存获取
            cached_data = CacheService.get(cache_key)
            if cached_data is not None:
                from rest_framework.response import Response
                return Response(cached_data)
            
            # 调用原函数
            response = func(self, request, *args, **kwargs)
            
            # 缓存响应数据
            if response.status_code == 200:
                CacheService.set(cache_key, response.data, timeout)
            
            return response
        return wrapper
    return decorator
