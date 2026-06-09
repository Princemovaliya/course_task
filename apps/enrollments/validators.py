from django.core.exceptions import ValidationError

from apps.courses.models import Course

from .models import Enrollment


def check_duplicate(student, course):
    """Rule 1 — block a second active enrollment in the same course."""
    if Enrollment.objects.filter(
        student=student, course=course, status=Enrollment.Status.ACTIVE
    ).exists():
        raise ValidationError("You are already enrolled in this course.")


def check_capacity(course):
    """Rule 2 — course must have remaining seats."""
    active_count = Enrollment.objects.filter(
        course=course, status=Enrollment.Status.ACTIVE
    ).count()
    if active_count >= course.max_capacity:
        raise ValidationError("This course has reached its maximum capacity.")


def check_schedule_conflict(student, new_course):
    """
    Rule 3 — no overlapping time windows with other active enrollments.

    Overlap exists when: existing.start < new.end AND existing.end > new.start
    """
    enrolled_courses = Course.objects.filter(
        enrollments__student=student,
        enrollments__status=Enrollment.Status.ACTIVE,
    ).exclude(pk=new_course.pk)
    conflict = enrolled_courses.filter(
        start_datetime__lt=new_course.end_datetime,
        end_datetime__gt=new_course.start_datetime,
    ).first()
    if conflict:
        raise ValidationError(
            f"Schedule conflict with '{conflict.title}' "
            f"({conflict.start_datetime} – {conflict.end_datetime})."
        )
