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

LOCATION_UNAVAILABLE = "Location service is unavailable. Please try again later."

def _normalize_location(attrs, instance=None):
    country = attrs.get("country", getattr(instance, "country", ""))
    state = attrs.get("state", getattr(instance, "state", ""))
    city = attrs.get("city", getattr(instance, "city", ""))
    try:
        validated = validate_location(country, state, city)
    except LocationAPIError:
        raise serializers.ValidationError(LOCATION_UNAVAILABLE)
    except DRFValidationError:
        raise
    attrs.update(validated)

class CourseSerializer(serializers.ModelSerializer):
    instructor_email = serializers.EmailField(source="instructor.email", read_only=True)

    class Meta:
        model = Course
        fields = (
            "id", "instructor", "instructor_email", "title", "description",
            "max_capacity", "start_datetime", "end_datetime",
            "country", "state", "city", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "instructor", "created_at", "updated_at")


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "title", "description", "max_capacity", "start_datetime",
            "end_datetime", "country", "state", "city", "is_active",
        )

    def validate(self, attrs):
        start, end = attrs.get("start_datetime"), attrs.get("end_datetime")
        if start and end:
            validate_course_starts_in_future(start)
            validate_course_time_window(start, end)
        _normalize_location(attrs)
        validate_instructor_course_overlap(
            instructor=self.context["request"].user,
            start_datetime=start,
            end_datetime=end,
        )
        return attrs
    
    def create(self, validated_data):
        validated_data["instructor"] = self.context["request"].user
        return super().create(validated_data)


class CourseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "title", "description", "max_capacity", "start_datetime",
            "end_datetime", "country", "state", "city", "is_active",
        )

    def validate(self, attrs):
        instance = self.instance
        start = attrs.get("start_datetime", instance.start_datetime)
        end = attrs.get("end_datetime", instance.end_datetime)

        validate_course_time_window(start, end)

        if "max_capacity" in attrs:
            validate_capacity_not_decreased(instance, attrs["max_capacity"])

        if any(attrs.get(f) not in (None, getattr(instance, f)) for f in ("start_datetime", "end_datetime")):
            raise serializers.ValidationError({
                "start_datetime": "Course time cannot be changed after creation.",
                "end_datetime": "Course time cannot be changed after creation.",
            })

        if {"country", "state", "city"} & attrs.keys():
            _normalize_location(attrs, instance=instance)

        validate_instructor_course_overlap(
            instructor=instance.instructor,
            start_datetime=start,
            end_datetime=end,
            exclude_course=instance,
        )
        return attrs