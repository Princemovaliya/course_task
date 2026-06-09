from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.courses.tests.factories import create_course, create_instructor, create_student
from apps.courses.tests.utils import get_results
from apps.enrollments.models import Enrollment

pytestmark = pytest.mark.django_db

VALIDATED_LOCATION = {"country": "IN", "state": "GJ", "city": "Ahmedabad"}

COURSE_PAYLOAD = {
    "title": "Python Basics",
    "description": "Learn Python",
    "max_capacity": 25,
    "start_datetime": (timezone.now() + timezone.timedelta(days=10)).isoformat(),
    "end_datetime": (timezone.now() + timezone.timedelta(days=10, hours=3)).isoformat(),
    "country": "IN",
    "state": "GJ",
    "city": "Ahmedabad",
}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def instructor():
    return create_instructor()


@pytest.fixture
def other_instructor():
    return create_instructor(email="other@example.com")


@pytest.fixture
def student():
    return create_student()


@patch("apps.courses.serializers.validate_location", return_value=VALIDATED_LOCATION)
def test_instructor_can_create_course(mock_validate, api_client, instructor):
    api_client.force_authenticate(user=instructor)
    response = api_client.post("/api/courses/", COURSE_PAYLOAD, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "Python Basics"
    mock_validate.assert_called_once()


def test_course_create_page_is_public(api_client):
    response = api_client.get("/courses/create/")
    assert response.status_code == status.HTTP_200_OK
    content = response.content.decode()
    assert "Create a Course" in content
    assert "sessionStorage.access_token" in content


@patch("apps.courses.serializers.validate_location", return_value=VALIDATED_LOCATION)
def test_instructor_cannot_create_overlapping_course(mock_validate, api_client, instructor):
    existing_course = create_course(instructor)
    api_client.force_authenticate(user=instructor)

    payload = {
        **COURSE_PAYLOAD,
        "start_datetime": existing_course.start_datetime.isoformat(),
        "end_datetime": existing_course.end_datetime.isoformat(),
    }
    response = api_client.post("/api/courses/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "overlaps" in str(response.data).lower()


@patch("apps.courses.serializers.validate_location", return_value=VALIDATED_LOCATION)
def test_other_instructor_can_create_same_time_course(mock_validate, api_client, instructor, other_instructor):
    existing_course = create_course(instructor)
    api_client.force_authenticate(user=other_instructor)

    payload = {
        **COURSE_PAYLOAD,
        "start_datetime": existing_course.start_datetime.isoformat(),
        "end_datetime": existing_course.end_datetime.isoformat(),
    }
    response = api_client.post("/api/courses/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED


@patch("apps.courses.serializers.validate_location", return_value=VALIDATED_LOCATION)
def test_student_cannot_create_course(mock_validate, api_client, student):
    api_client.force_authenticate(user=student)
    response = api_client.post("/api/courses/", COURSE_PAYLOAD, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_student_can_list_active_courses(api_client, student, instructor):
    create_course(instructor, is_active=True)
    create_course(instructor, is_active=False, title="Hidden")
    api_client.force_authenticate(user=student)

    response = api_client.get("/api/courses/")
    assert response.status_code == status.HTTP_200_OK
    assert len(get_results(response)) == 1


def test_instructor_cannot_list_all_courses(api_client, instructor):
    create_course(instructor)
    api_client.force_authenticate(user=instructor)

    response = api_client.get("/api/courses/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_instructor_can_list_own_courses_via_mine(api_client, instructor, other_instructor):
    create_course(instructor, title="Mine")
    create_course(other_instructor, title="Not Mine")
    api_client.force_authenticate(user=instructor)

    response = api_client.get("/api/courses/mine/")
    assert response.status_code == status.HTTP_200_OK
    assert len(get_results(response)) == 1
    results = get_results(response)
    assert results[0]["title"] == "Mine"


def test_instructor_cannot_retrieve_other_instructor_course(api_client, instructor, other_instructor):
    course = create_course(other_instructor)
    api_client.force_authenticate(user=instructor)

    response = api_client.get(f"/api/courses/{course.id}/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_student_can_retrieve_any_course(api_client, student, instructor):
    course = create_course(instructor)
    api_client.force_authenticate(user=student)

    response = api_client.get(f"/api/courses/{course.id}/")
    assert response.status_code == status.HTTP_200_OK


@patch("apps.courses.serializers.validate_location", return_value=VALIDATED_LOCATION)
def test_course_create_writes_audit_log(mock_validate, api_client, instructor):
    api_client.force_authenticate(user=instructor)
    api_client.post("/api/courses/", COURSE_PAYLOAD, format="json")

    assert AuditLog.objects.filter(action=AuditLog.Action.COURSE_CREATED).count() == 1


@patch("apps.courses.serializers.validate_location", return_value=VALIDATED_LOCATION)
def test_course_update_writes_audit_log(mock_validate, api_client, instructor):
    course = create_course(instructor)
    api_client.force_authenticate(user=instructor)

    api_client.patch(
        f"/api/courses/{course.id}/",
        {"title": "Updated Title"},
        format="json",
    )
    assert AuditLog.objects.filter(action=AuditLog.Action.COURSE_UPDATED).count() == 1


def test_course_update_allows_non_locking_fields(api_client, instructor):
    course = create_course(instructor)
    api_client.force_authenticate(user=instructor)

    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {"title": "Updated Title"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    course.refresh_from_db()
    assert course.title == "Updated Title"


def test_course_update_rejects_capacity_reduction(api_client, instructor):
    course = create_course(instructor, max_capacity=25)
    api_client.force_authenticate(user=instructor)

    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {"max_capacity": 20},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "capacity" in str(response.data).lower()


def test_course_update_allows_capacity_increase(api_client, instructor):
    course = create_course(instructor, max_capacity=25)
    api_client.force_authenticate(user=instructor)

    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {"max_capacity": 40},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    course.refresh_from_db()
    assert course.max_capacity == 40


def test_course_update_rejects_time_change(api_client, instructor):
    course = create_course(instructor)
    api_client.force_authenticate(user=instructor)

    response = api_client.patch(
        f"/api/courses/{course.id}/",
        {
            "start_datetime": (course.start_datetime + timezone.timedelta(hours=1)).isoformat()
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be changed" in str(response.data).lower()


def test_course_update_rejects_overlap_with_same_instructor(api_client, instructor):
    course_a = create_course(
        instructor,
        title="Course A",
        start_datetime=timezone.now() + timezone.timedelta(days=5, hours=9),
        end_datetime=timezone.now() + timezone.timedelta(days=5, hours=11),
    )
    create_course(
        instructor,
        title="Course B",
        start_datetime=timezone.now() + timezone.timedelta(days=5, hours=10),
        end_datetime=timezone.now() + timezone.timedelta(days=5, hours=12),
    )
    api_client.force_authenticate(user=instructor)

    response = api_client.patch(
        f"/api/courses/{course_a.id}/",
        {"title": "Updated Course A"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "overlaps" in str(response.data).lower()


def test_instructor_can_view_own_course_enrollments(api_client, instructor, student):
    course = create_course(instructor)
    Enrollment.objects.create(student=student, course=course)
    api_client.force_authenticate(user=instructor)

    response = api_client.get(f"/api/courses/{course.id}/enrollments/")
    assert response.status_code == status.HTTP_200_OK
    assert len(get_results(response)) == 1
    assert get_results(response)[0]["student_email"] == student.email


def test_instructor_cannot_view_other_course_enrollments(api_client, instructor, other_instructor, student):
    course = create_course(other_instructor)
    Enrollment.objects.create(student=student, course=course)
    api_client.force_authenticate(user=instructor)

    response = api_client.get(f"/api/courses/{course.id}/enrollments/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_student_can_filter_courses_by_country(api_client, student, instructor):
    create_course(instructor, country="IN", city="Ahmedabad")
    create_course(instructor, country="US", city="New York", state="NY")
    api_client.force_authenticate(user=student)

    response = api_client.get("/api/courses/?country=IN")
    assert response.status_code == status.HTTP_200_OK
    assert len(get_results(response)) == 1
    assert get_results(response)[0]["country"] == "IN"
