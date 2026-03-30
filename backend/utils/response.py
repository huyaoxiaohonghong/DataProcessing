"""
统一 API 响应工具
Standardized API response helpers
"""
from rest_framework.response import Response
from rest_framework import status


class ApiResponse:
    """统一 API 响应格式"""

    @staticmethod
    def success(data=None, message='操作成功', code=200, http_status=status.HTTP_200_OK):
        """成功响应"""
        response = {
            'code': code,
            'message': message,
        }
        if data is not None:
            response['data'] = data
        return Response(response, status=http_status)

    @staticmethod
    def created(data=None, message='创建成功'):
        """创建成功响应"""
        return ApiResponse.success(data=data, message=message, http_status=status.HTTP_201_CREATED)

    @staticmethod
    def error(message='操作失败', code=400, http_status=status.HTTP_400_BAD_REQUEST, errors=None):
        """错误响应"""
        response = {
            'code': code,
            'message': message,
        }
        if errors is not None:
            response['errors'] = errors
        return Response(response, status=http_status)

    @staticmethod
    def not_found(message='资源不存在'):
        """404 响应"""
        return ApiResponse.error(message=message, code=404, http_status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def forbidden(message='权限不足'):
        """403 响应"""
        return ApiResponse.error(message=message, code=403, http_status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def unauthorized(message='未授权'):
        """401 响应"""
        return ApiResponse.error(message=message, code=401, http_status=status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def server_error(message='服务器内部错误'):
        """500 响应"""
        return ApiResponse.error(
            message=message, code=500,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
