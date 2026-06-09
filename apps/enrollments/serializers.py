from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.courses.models import Course

from .models import Enrollment
from .validators import check_capacity, check_duplicate, check_schedule_conflict


class EnrollmentReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for instructors viewing course enrollments."""

    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "student_email",
            "student_name",
            "status",
            "enrolled_at",
            "cancelled_at",
        )

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip()


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    """Student-facing enrollment detail returned from GET /api/enrollments/mine/."""

    course_id = serializers.UUIDField(source="course.id", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_start = serializers.DateTimeField(source="course.start_datetime", read_only=True)
    course_end = serializers.DateTimeField(source="course.end_datetime", read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "course_id",
            "course_title",
            "course_start",
            "course_end",
            "status",
            "enrolled_at",
            "cancelled_at",
        )


class EnrollmentCreateSerializer(serializers.Serializer):
    """Write serializer for POST /api/enrollments/ — runs all 3 rules atomically."""

    course = serializers.UUIDField()

    def validate_course(self, value):
        try:
            course = Course.objects.get(pk=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found.")
        if not course.is_active:
            raise serializers.ValidationError("This course is no longer available.")
        return value

    def create(self, validated_data):
        student = self.context["request"].user
        course_id = validated_data["course"]

        # Lock the course row so capacity checks are race-safe
        try:
            with transaction.atomic():
                course = Course.objects.select_for_update().get(pk=course_id)
                check_duplicate(student, course)
                check_capacity(course)
                check_schedule_conflict(student, course)
                enrollment = Enrollment.objects.create(student=student, course=course)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

        return enrollment


class EnrollmentCreateResponseSerializer(serializers.ModelSerializer):
    """Minimal response body after a successful enrollment."""

    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Enrollment
        fields = ("id", "course", "course_title", "status", "enrolled_at")
