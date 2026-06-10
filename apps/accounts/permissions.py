from rest_framework.permissions import BasePermission
from apps.accounts.models import User


class RolePermission(BasePermission):
    required_role = None

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == self.required_role
        )


class IsStudent(RolePermission):
    required_role = User.Role.STUDENT


class IsInstructor(RolePermission):
    required_role = User.Role.INSTRUCTOR