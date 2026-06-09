import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Enrollment(models.Model):
    """
    Links a student to a course.

    Partial unique constraint allows re-enrollment after cancellation (Phase 4).
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    # Set when status transitions to cancelled (Phase 4)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "enrollments"
        constraints = [
            # Only one active enrollment per student+course pair
            models.UniqueConstraint(
                fields=["student", "course"],
                condition=Q(status="active"),
                name="unique_active_enrollment",
            ),
        ]

    def __str__(self):
        return f"{self.student.email} → {self.course.title} ({self.status})"
