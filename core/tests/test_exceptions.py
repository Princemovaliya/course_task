import pytest
from rest_framework.exceptions import NotFound
from rest_framework.test import APIRequestFactory

from core.exceptions import custom_exception_handler

pytestmark = pytest.mark.django_db


def test_exception_handler_normalizes_not_found():
    factory = APIRequestFactory()
    request = factory.get("/api/courses/00000000-0000-0000-0000-000000000099/")
    exc = NotFound("Course not found.")
    response = custom_exception_handler(exc, {"request": request, "view": None})

    assert response.status_code == 404
    assert response.data == {"error": "Not Found", "detail": "Course not found."}
