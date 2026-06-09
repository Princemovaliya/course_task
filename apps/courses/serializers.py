from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.location.services import LocationAPIError, validate_location

from .models import Course
from .validators import (
    validate_capacity_not_decreased,
    validate_course_starts_in_future,
    validate_course_time_window,
    validate_instructor_course_overlap,
)


class CourseValidationMixin:
    LOCATION_ERROR_MESSAGE = (
        "Location service is unavailable. Please try again later."
    )

    def _validate_and_normalize_location(self, attrs, instance=None):
        country = attrs.get("country", getattr(instance, "country", ""))
        state = attrs.get("state", getattr(instance, "state", ""))
        city = attrs.get("city", getattr(instance, "city", ""))

        try:
            validated = validate_location(country, state, city)
        except LocationAPIError:
            raise serializers.ValidationError(self.LOCATION_ERROR_MESSAGE)
        except DRFValidationError:
            raise

        attrs["country"] = validated["country"]
        attrs["state"] = validated["state"]
        attrs["city"] = validated["city"]

    def _validate_instructor_overlap(
        self, *, instructor, start_datetime, end_datetime, exclude_course=None
    ):
        validate_instructor_course_overlap(
            instructor=instructor,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            exclude_course=exclude_course,
        )


class CourseSerializer(serializers.ModelSerializer):
    """Read serializer — used for list/retrieve responses."""

    instructor_email = serializers.EmailField(source="instructor.email", read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "instructor",
            "instructor_email",
            "title",
            "description",
            "max_capacity",
            "start_datetime",
            "end_datetime",
            "country",
            "state",
            "city",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "instructor", "created_at", "updated_at")


class CourseCreateSerializer(CourseValidationMixin, serializers.ModelSerializer):
    """Write serializer for POST /api/courses/ — validates location via Location API."""

    class Meta:
        model = Course
        fields = (
            "title",
            "description",
            "max_capacity",
            "start_datetime",
            "end_datetime",
            "country",
            "state",
            "city",
            "is_active",
        )

    def validate(self, attrs):
        start = attrs.get("start_datetime")
        end = attrs.get("end_datetime")
        if start is not None and end is not None:
            validate_course_starts_in_future(start)
            validate_course_time_window(start, end)

        self._validate_and_normalize_location(attrs)

        self._validate_instructor_overlap(
            instructor=self.context["request"].user,
            start_datetime=start,
            end_datetime=end,
        )
        return attrs

    def create(self, validated_data):
        # Instructor is set from the authenticated user in the view
        validated_data["instructor"] = self.context["request"].user
        return super().create(validated_data)


class CourseUpdateSerializer(CourseValidationMixin, serializers.ModelSerializer):
    """Partial update serializer for PATCH /api/courses/{id}/."""

    class Meta:
        model = Course
        fields = (
            "title",
            "description",
            "max_capacity",
            "start_datetime",
            "end_datetime",
            "country",
            "state",
            "city",
            "is_active",
        )

    def validate(self, attrs):
        instance = self.instance
        start = attrs.get("start_datetime", instance.start_datetime)
        end = attrs.get("end_datetime", instance.end_datetime)
        validate_course_time_window(start, end)

        if "max_capacity" in attrs:
            validate_capacity_not_decreased(instance, attrs["max_capacity"])

        time_fields_changed = any(
            field in attrs
            and attrs[field] != getattr(instance, field)
            for field in ("start_datetime", "end_datetime")
        )
        if time_fields_changed:
            raise serializers.ValidationError(
                {
                    "start_datetime": "Course time cannot be changed after creation.",
                    "end_datetime": "Course time cannot be changed after creation.",
                }
            )

        if {"country", "state", "city"} & set(attrs.keys()):
            self._validate_and_normalize_location(attrs, instance=instance)

        self._validate_instructor_overlap(
            instructor=instance.instructor,
            start_datetime=start,
            end_datetime=end,
            exclude_course=instance,
        )

        return attrs
