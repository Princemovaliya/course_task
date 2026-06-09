from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Course


def validate_course_starts_in_future(start_datetime):
    if start_datetime < timezone.now():
        raise ValidationError(
            {"start_datetime": "Course start datetime cannot be in the past."}
        )


def validate_course_time_window(start_datetime, end_datetime):
    if end_datetime <= start_datetime:
        raise ValidationError(
            {"end_datetime": "End datetime must be after start datetime."}
        )


def validate_instructor_course_overlap(
    *, instructor, start_datetime, end_datetime, exclude_course=None
):
    queryset = Course.objects.filter(instructor=instructor)

    if exclude_course is not None:
        queryset = queryset.exclude(pk=exclude_course.pk)

    conflict = queryset.filter(
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
    ).first()
    if conflict:
        raise ValidationError(
            f"Course time overlaps with '{conflict.title}' "
            f"({conflict.start_datetime} - {conflict.end_datetime})."
        )


def validate_capacity_not_decreased(instance, max_capacity):
    if max_capacity < instance.max_capacity:
        raise ValidationError(
            {"max_capacity": "You cannot reduce capacity after creation."}
        )
