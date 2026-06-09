from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.location.services import LocationAPIError, validate_location

from .models import Course


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


class CourseCreateSerializer(serializers.ModelSerializer):
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
        # Schedule sanity check
        start = attrs.get("start_datetime")
        end = attrs.get("end_datetime")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_datetime": "End datetime must be after start datetime."}
            )

        # Verify country/state/city exist in the upstream Location API
        country = attrs.get("country", "")
        state = attrs.get("state", "")
        city = attrs.get("city", "")
        try:
            validated = validate_location(country, state, city)
        except LocationAPIError:
            raise serializers.ValidationError(
                "Location service is unavailable. Please try again later."
            )
        except DRFValidationError:
            raise

        # Normalize to canonical codes returned by the Location API
        attrs["country"] = validated["country"]
        attrs["state"] = validated["state"]
        attrs["city"] = validated["city"]
        return attrs

    def create(self, validated_data):
        # Instructor is set from the authenticated user in the view
        validated_data["instructor"] = self.context["request"].user
        return super().create(validated_data)


class CourseUpdateSerializer(serializers.ModelSerializer):
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
        if end <= start:
            raise serializers.ValidationError(
                {"end_datetime": "End datetime must be after start datetime."}
            )

        # Re-validate location only when any location field is being changed
        location_fields = {"country", "state", "city"}
        if location_fields & set(attrs.keys()):
            country = attrs.get("country", instance.country)
            state = attrs.get("state", instance.state)
            city = attrs.get("city", instance.city)
            try:
                validated = validate_location(country, state, city)
            except LocationAPIError:
                raise serializers.ValidationError(
                    "Location service is unavailable. Please try again later."
                )
            except DRFValidationError:
                raise

            attrs["country"] = validated["country"]
            attrs["state"] = validated["state"]
            attrs["city"] = validated["city"]

        return attrs
