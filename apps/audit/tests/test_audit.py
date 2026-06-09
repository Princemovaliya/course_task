import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.courses.tests.factories import create_course, create_instructor, create_student

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        email="admin@example.com",
        password="password123",
        role=User.Role.STUDENT,
        first_name="Admin",
        last_name="User",
    )


def test_audit_endpoint_requires_admin(api_client):
    student = create_student()
    api_client.force_authenticate(user=student)
    response = api_client.get("/api/audit/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_list_audit_logs(api_client, admin_user):
    instructor = create_instructor()
    course = create_course(instructor)
    AuditLog.objects.create(
        actor=instructor,
        action=AuditLog.Action.COURSE_CREATED,
        target_type="Course",
        target_id=course.id,
        metadata={"title": course.title},
    )
    api_client.force_authenticate(user=admin_user)

    response = api_client.get("/api/audit/")
    assert response.status_code == status.HTTP_200_OK
    actions = [row["action"] for row in response.data["results"]]
    assert "course_created" in actions
