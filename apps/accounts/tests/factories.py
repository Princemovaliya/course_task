import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")
    first_name = "Test"
    last_name = "User"
    role = User.Role.STUDENT


class StudentFactory(UserFactory):
    role = User.Role.STUDENT


class InstructorFactory(UserFactory):
    role = User.Role.INSTRUCTOR


class AdminFactory(UserFactory):
    role = User.Role.STUDENT
    is_staff = True
    is_superuser = True
