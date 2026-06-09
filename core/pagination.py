from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """Consistent paginated list responses across all list endpoints."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
