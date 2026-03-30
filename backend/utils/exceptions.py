"""
自定义异常处理器
Custom exception handler for DRF
"""
import logging
from rest_framework.views import exception_handler
from rest_framework import status

logger = logging.getLogger('apps')


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    统一异常响应格式为 {code, message, errors}
    """
    response = exception_handler(exc, context)

    if response is not None:
        # 提取错误信息
        if isinstance(response.data, dict):
            # DRF 验证错误通常是 dict
            detail = response.data.get('detail', None)
            if detail:
                message = str(detail)
                errors = None
            else:
                # 字段验证错误
                message = '请求参数有误'
                errors = response.data
        elif isinstance(response.data, list):
            message = '; '.join(str(e) for e in response.data)
            errors = None
        else:
            message = str(response.data)
            errors = None

        # 统一格式
        custom_data = {
            'code': response.status_code,
            'message': message,
        }
        if errors:
            custom_data['errors'] = errors

        response.data = custom_data
    else:
        # 未处理的异常 → 记录日志并返回 500
        logger.exception(
            f"Unhandled exception in {context.get('view', 'unknown')}: {exc}"
        )
        from rest_framework.response import Response
        response = Response(
            {'code': 500, 'message': '服务器内部错误'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
