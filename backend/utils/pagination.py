"""
自定义分页器
Custom pagination classes for DRF
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    标准分页器
    统一分页响应格式，与前端 Ant Design Table 对齐
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': {
                'results': data,
                'pagination': {
                    'total': self.page.paginator.count,
                    'page': self.page.number,
                    'page_size': self.get_page_size(self.request),
                    'total_pages': self.page.paginator.num_pages,
                }
            }
        })
