import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Immutable record of significant system events for compliance and debugging."""

    class Action(models.TextChoices):
        COURSE_CREATED = "course_created", "Course Created"
        COURSE_UPDATED = "course_updated", "Course Updated"
        STUDENT_ENROLLED = "student_enrolled", "Student Enrolled"
        ENROLLMENT_CANCELLED = "enrollment_cancelled", "Enrollment Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Actor may be null if the user account was deleted after the event
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50, choices=Action.choices)
    # Polymorphic reference — stores model name + UUID of the affected object
    target_type = models.CharField(max_length=50)
    target_id = models.UUIDField()
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on {self.target_type}({self.target_id})"
