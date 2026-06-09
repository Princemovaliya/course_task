from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.courses.tests.factories import create_course, create_instructor, create_student
from apps.enrollments.models import Enrollment
from apps.enrollments.validators import (
    check_capacity,
    check_duplicate,
    check_schedule_conflict,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student():
    return create_student()


@pytest.fixture
def other_student():
    return create_student(email="other@example.com")


@pytest.fixture
def instructor():
    return create_instructor()


@pytest.fixture
def course(instructor):
    return create_course(instructor)


# --- Unit tests: validation rules in isolation ---


def test_check_duplicate_raises_when_active_enrollment_exists(student, course):
    Enrollment.objects.create(student=student, course=course, status=Enrollment.Status.ACTIVE)
    with pytest.raises(ValidationError, match="already enrolled"):
        check_duplicate(student, course)


def test_check_duplicate_allows_re_enrollment_after_cancel(student, course):
    Enrollment.objects.create(student=student, course=course, status=Enrollment.Status.CANCELLED)
    check_duplicate(student, course)  # should not raise


def test_check_capacity_raises_when_full(student, instructor):
    small_course = create_course(instructor, max_capacity=1)
    other = create_student(email="full@example.com")
    Enrollment.objects.create(student=other, course=small_course, status=Enrollment.Status.ACTIVE)

    with pytest.raises(ValidationError, match="maximum capacity"):
        check_capacity(small_course)


def test_check_capacity_passes_when_seats_available(student, course):
    check_capacity(course)  # max_capacity=30, 0 enrolled


def test_check_schedule_conflict_detects_overlap(student, instructor):
    now = timezone.now()
    course_a = create_course(
        instructor,
        title="Course A",
        start_datetime=now + timedelta(days=1),
        end_datetime=now + timedelta(days=1, hours=2),
    )
    course_b = create_course(
        instructor,
        title="Course B",
        start_datetime=now + timedelta(days=1, hours=1),
        end_datetime=now + timedelta(days=1, hours=3),
    )
    Enrollment.objects.create(student=student, course=course_a, status=Enrollment.Status.ACTIVE)

    with pytest.raises(ValidationError, match="Schedule conflict"):
        check_schedule_conflict(student, course_b)


def test_check_schedule_conflict_passes_when_no_overlap(student, instructor):
    now = timezone.now()
    course_a = create_course(
        instructor,
        title="Morning",
        start_datetime=now + timedelta(days=1, hours=9),
        end_datetime=now + timedelta(days=1, hours=11),
    )
    course_b = create_course(
        instructor,
        title="Afternoon",
        start_datetime=now + timedelta(days=1, hours=14),
        end_datetime=now + timedelta(days=1, hours=16),
    )
    Enrollment.objects.create(student=student, course=course_a, status=Enrollment.Status.ACTIVE)
    check_schedule_conflict(student, course_b)  # should not raise
