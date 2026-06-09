from drf_spectacular.utils import OpenApiExample

REGISTER_EXAMPLE = OpenApiExample(
    "Register student",
    value={
        "email": "student@example.com",
        "password": "password123",
        "role": "student",
        "first_name": "Jane",
        "last_name": "Doe",
    },
    request_only=True,
)

LOGIN_EXAMPLE = OpenApiExample(
    "Login",
    value={"email": "student@example.com", "password": "password123"},
    request_only=True,
)

LOGOUT_EXAMPLE = OpenApiExample(
    "Logout",
    value={"refresh": "<refresh-token>"},
    request_only=True,
)

COURSE_CREATE_EXAMPLE = OpenApiExample(
    "Create course",
    value={
        "title": "Python Basics",
        "description": "Introductory Python course",
        "max_capacity": 25,
        "start_datetime": "2026-07-01T09:00:00Z",
        "end_datetime": "2026-07-01T12:00:00Z",
        "country": "IN",
        "state": "GJ",
        "city": "Ahmedabad",
    },
    request_only=True,
)

COURSE_UPDATE_EXAMPLE = OpenApiExample(
    "Update course",
    value={"title": "Advanced Python", "max_capacity": 30},
    request_only=True,
)

ENROLLMENT_CREATE_EXAMPLE = OpenApiExample(
    "Enroll in course",
    value={"course": "00000000-0000-0000-0000-000000000001"},
    request_only=True,
)
