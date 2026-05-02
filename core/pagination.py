"""
Shared pagination classes for API responses.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """Standard pagination: 20 items per page, configurable via query param."""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class SmallResultsPagination(PageNumberPagination):
    """Small pagination for lightweight endpoints like notifications."""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
