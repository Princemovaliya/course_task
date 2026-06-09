from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsInstructor, IsStudent
from apps.enrollments.serializers import EnrollmentReadSerializer
from core.openapi_examples import COURSE_CREATE_EXAMPLE, COURSE_UPDATE_EXAMPLE
from core.pagination import StandardResultsPagination

from .filters import CourseFilter
from .models import Course
from .serializers import (
    CourseCreateSerializer,
    CourseSerializer,
    CourseUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        description="Students: browse all active courses with optional filters.",
        parameters=[
            OpenApiParameter(
                name="country",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter courses by ISO2 country code (e.g. IN).",
            ),
            OpenApiParameter(
                name="state",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter courses by state code (e.g. GJ).",
            ),
            OpenApiParameter(
                name="city",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter courses by city name (e.g. Ahmedabad).",
            ),
            OpenApiParameter(
                name="start_datetime",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter courses starting on or after this datetime.",
            ),
        ],
        responses={200: CourseSerializer(many=True)},
    ),
    retrieve=extend_schema(
        description=(
            "Role-split retrieve: students may fetch any course by ID; "
            "instructors receive 404 for courses they do not own."
        ),
        responses={200: CourseSerializer},
    ),
    create=extend_schema(
        description="Instructors: create a new course (location validated).",
        examples=[COURSE_CREATE_EXAMPLE],
    ),
    partial_update=extend_schema(
        description="Instructors: update own course only.",
        examples=[COURSE_UPDATE_EXAMPLE],
    ),
)
class CourseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Role-scoped course endpoints.

    Access rules are enforced via get_queryset() + per-action permissions:
    - Students list/browse all active courses
    - Instructors manage only their own courses (404 for others)
    """

    filter_backends = [DjangoFilterBackend]
    filterset_class = CourseFilter
    pagination_class = StandardResultsPagination
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return CourseCreateSerializer
        if self.action in ("partial_update", "update"):
            return CourseUpdateSerializer
        return CourseSerializer

    def get_permissions(self):
        # Different roles are allowed per action. See the access matrix in the README.
        if self.action == "list":
            return [IsAuthenticated(), IsStudent()]
        if self.action == "create":
            return [IsAuthenticated(), IsInstructor()]
        if self.action in ("partial_update", "update", "mine", "enrollments"):
            return [IsAuthenticated(), IsInstructor()]
        # retrieve: both students and instructors (queryset scoping differs)
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        if user.role == "student":
            if self.action == "list":
                return Course.objects.filter(is_active=True).select_related("instructor")
            return Course.objects.all().select_related("instructor")

        if user.role == "instructor":
            return Course.objects.filter(instructor=user).select_related("instructor")

        return Course.objects.none()

    def update(self, request, *args, **kwargs):
        # PATCH only - no full PUT replacement
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        responses={200: CourseSerializer(many=True)},
        description="Instructors: list all courses owned by the authenticated user.",
    )
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """GET /api/courses/mine/ - instructor's own course list."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CourseSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CourseSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={200: EnrollmentReadSerializer(many=True)},
        description="Instructors: view enrollments for an owned course.",
    )
    @action(detail=True, methods=["get"], url_path="enrollments")
    def enrollments(self, request, pk=None):
        """GET /api/courses/{id}/enrollments/ - enrollment roster for own course."""
        course = self.get_object()  # 404 if not instructor's course
        enrollments = course.enrollments.select_related("student").order_by("-enrolled_at")
        page = self.paginate_queryset(enrollments)
        if page is not None:
            serializer = EnrollmentReadSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EnrollmentReadSerializer(enrollments, many=True)
        return Response(serializer.data)
