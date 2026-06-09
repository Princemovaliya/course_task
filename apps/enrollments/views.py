from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsStudent
from apps.audit.models import AuditLog
from apps.audit.utils import log_event
from core.openapi_examples import ENROLLMENT_CREATE_EXAMPLE
from core.pagination import StandardResultsPagination
from core.throttling import EnrollmentUserRateThrottle

from .models import Enrollment
from .serializers import (
    EnrollmentCreateResponseSerializer,
    EnrollmentCreateSerializer,
    StudentEnrollmentSerializer,
)


@extend_schema_view(
    create=extend_schema(
        request=EnrollmentCreateSerializer,
        responses={201: EnrollmentCreateResponseSerializer},
        description="Students: enroll in a course (all 3 validation rules enforced).",
        examples=[ENROLLMENT_CREATE_EXAMPLE],
    ),
    destroy=extend_schema(
        description="Students: cancel own active enrollment (soft-delete via status).",
    ),
)
class EnrollmentViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Student enrollment lifecycle.

    - POST   /api/enrollments/       → enroll
    - GET    /api/enrollments/mine/  → list own enrollments
    - DELETE /api/enrollments/{id}/  → cancel own enrollment

    Instructors view enrollments via /api/courses/{id}/enrollments/ instead.
    """

    http_method_names = ["get", "post", "delete", "head", "options"]
    pagination_class = StandardResultsPagination
    throttle_classes = [EnrollmentUserRateThrottle]

    def get_permissions(self):
        # All enrollment endpoints are student-only
        return [IsAuthenticated(), IsStudent()]

    def get_queryset(self):
        # Students can only ever access their own enrollment rows
        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related("course")

    def get_serializer_class(self):
        if self.action == "create":
            return EnrollmentCreateSerializer
        return StudentEnrollmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()

        # Audit from view — signals cannot detect status transitions reliably
        log_event(
            actor=request.user,
            action=AuditLog.Action.STUDENT_ENROLLED,
            target=enrollment,
            metadata={
                "course_title": enrollment.course.title,
                "student_email": request.user.email,
            },
        )

        response_serializer = EnrollmentCreateResponseSerializer(enrollment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        enrollment = self.get_object()

        if enrollment.status == Enrollment.Status.CANCELLED:
            return Response(
                {"detail": "Enrollment is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Soft cancel — keep the row so re-enrollment history is preserved
        enrollment.status = Enrollment.Status.CANCELLED
        enrollment.cancelled_at = timezone.now()
        enrollment.save(update_fields=["status", "cancelled_at"])

        log_event(
            actor=request.user,
            action=AuditLog.Action.ENROLLMENT_CANCELLED,
            target=enrollment,
            metadata={
                "course_title": enrollment.course.title,
                "student_email": request.user.email,
            },
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=["active", "cancelled"],
                description="Filter enrollments by status.",
            ),
        ],
        responses={200: StudentEnrollmentSerializer(many=True)},
        description="Students: list own enrollments, optionally filtered by status.",
    )
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """GET /api/enrollments/mine/ — student's own enrollment list."""
        queryset = self.get_queryset().order_by("-enrolled_at")

        status_filter = request.query_params.get("status")
        if status_filter:
            if status_filter not in (
                Enrollment.Status.ACTIVE,
                Enrollment.Status.CANCELLED,
            ):
                return Response(
                    {"detail": "Invalid status. Use 'active' or 'cancelled'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_filter)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = StudentEnrollmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StudentEnrollmentSerializer(queryset, many=True)
        return Response(serializer.data)
