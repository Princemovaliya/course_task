from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.courses.models import Course


def create_instructor(email="instructor@example.com"):
    return User.objects.create_user(
        email=email,
        password="password123",
        role=User.Role.INSTRUCTOR,
        first_name="Test",
        last_name="Instructor",
    )


def create_student(email="student@example.com"):
    return User.objects.create_user(
        email=email,
        password="password123",
        role=User.Role.STUDENT,
        first_name="Test",
        last_name="Student",
    )


def create_course(instructor, **overrides):
    now = timezone.now()
    defaults = {
        "instructor": instructor,
        "title": "Test Course",
        "description": "Test course description",
        "max_capacity": 30,
        "start_datetime": now + timedelta(days=7),
        "end_datetime": now + timedelta(days=7, hours=2),
        "country": "IN",
        "state": "GJ",
        "city": "Ahmedabad",
        "is_active": True,
    }
    defaults.update(overrides)
    return Course.objects.create(**defaults)
