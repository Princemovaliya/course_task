from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser

from core.pagination import StandardResultsPagination

from .models import AuditLog
from .serializers import AuditLogSerializer


@extend_schema(
    description="Admin-only read-only list of all audit log entries.",
    responses={200: AuditLogSerializer(many=True)},
)
class AuditLogListView(ListAPIView):
    """GET /api/audit/ — verify audit trails without Django Admin."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    pagination_class = StandardResultsPagination
    queryset = AuditLog.objects.select_related("actor").order_by("-timestamp")
