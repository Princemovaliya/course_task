from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.audit.models import AuditLog
from apps.courses.tests.factories import create_course, create_instructor, create_student
from apps.courses.tests.utils import get_results
from apps.enrollments.models import Enrollment

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


def test_student_can_enroll(api_client, student, course):
    api_client.force_authenticate(user=student)
    response = api_client.post(
        "/api/enrollments/",
        {"course": str(course.id)},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == "active"
    assert AuditLog.objects.filter(action=AuditLog.Action.STUDENT_ENROLLED).count() == 1


def test_instructor_cannot_enroll(api_client, instructor, course):
    api_client.force_authenticate(user=instructor)
    response = api_client.post(
        "/api/enrollments/",
        {"course": str(course.id)},
        format="json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_student_can_view_own_enrollments(api_client, student, course):
    Enrollment.objects.create(student=student, course=course)
    api_client.force_authenticate(user=student)

    response = api_client.get("/api/enrollments/mine/")
    assert response.status_code == status.HTTP_200_OK
    assert len(get_results(response)) == 1


def test_student_cannot_access_other_students_enrollments_via_mine(api_client, student, other_student, instructor):
    """Permission boundary: mine endpoint only returns the authenticated student's rows."""
    course = create_course(instructor)
    Enrollment.objects.create(student=other_student, course=course)
    api_client.force_authenticate(user=student)

    response = api_client.get("/api/enrollments/mine/")
    assert response.status_code == status.HTTP_200_OK
    assert len(get_results(response)) == 0


def test_student_cannot_cancel_other_students_enrollment(api_client, student, other_student, course):
    enrollment = Enrollment.objects.create(student=other_student, course=course)
    api_client.force_authenticate(user=student)

    response = api_client.delete(f"/api/enrollments/{enrollment.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_student_can_cancel_own_enrollment(api_client, student, course):
    enrollment = Enrollment.objects.create(student=student, course=course)
    api_client.force_authenticate(user=student)

    response = api_client.delete(f"/api/enrollments/{enrollment.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    enrollment.refresh_from_db()
    assert enrollment.status == Enrollment.Status.CANCELLED
    assert enrollment.cancelled_at is not None
    assert AuditLog.objects.filter(action=AuditLog.Action.ENROLLMENT_CANCELLED).count() == 1


def test_mine_endpoint_filters_by_status(api_client, student, instructor):
    active_course = create_course(instructor, title="Active Course")
    cancelled_course = create_course(
        instructor,
        title="Cancelled Course",
        start_datetime=timezone.now() + timedelta(days=14),
        end_datetime=timezone.now() + timedelta(days=14, hours=2),
    )
    Enrollment.objects.create(student=student, course=active_course, status=Enrollment.Status.ACTIVE)
    Enrollment.objects.create(
        student=student,
        course=cancelled_course,
        status=Enrollment.Status.CANCELLED,
    )
    api_client.force_authenticate(user=student)

    active_response = api_client.get("/api/enrollments/mine/?status=active")
    assert len(get_results(active_response)) == 1
    assert get_results(active_response)[0]["status"] == "active"

    cancelled_response = api_client.get("/api/enrollments/mine/?status=cancelled")
    assert len(get_results(cancelled_response)) == 1
    assert get_results(cancelled_response)[0]["status"] == "cancelled"


def test_full_enrollment_flow_enroll_conflict_cancel_re_enroll(api_client, student, instructor):
    """Integration: enroll → duplicate blocked → cancel → re-enroll succeeds."""
    course = create_course(instructor)
    api_client.force_authenticate(user=student)

    # Enroll successfully
    first = api_client.post("/api/enrollments/", {"course": str(course.id)}, format="json")
    assert first.status_code == status.HTTP_201_CREATED

    # Duplicate blocked
    duplicate = api_client.post("/api/enrollments/", {"course": str(course.id)}, format="json")
    assert duplicate.status_code == status.HTTP_400_BAD_REQUEST

    # Cancel
    enrollment_id = first.data["id"]
    cancel = api_client.delete(f"/api/enrollments/{enrollment_id}/")
    assert cancel.status_code == status.HTTP_204_NO_CONTENT

    # Re-enroll after cancellation
    re_enroll = api_client.post("/api/enrollments/", {"course": str(course.id)}, format="json")
    assert re_enroll.status_code == status.HTTP_201_CREATED
