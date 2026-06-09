from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit.models import AuditLog
from apps.audit.utils import log_event

from .models import Course


@receiver(post_save, sender=Course)
def audit_course_save(sender, instance, created, **kwargs):
    """
    Write audit log entries when a course is created or updated.

    Triggered automatically after every Course save — keeps views thin.
    """
    action = (
        AuditLog.Action.COURSE_CREATED if created else AuditLog.Action.COURSE_UPDATED
    )
    # Actor comes from middleware thread-local is not available; use instructor as actor
    log_event(
        actor=instance.instructor,
        action=action,
        target=instance,
        metadata={"title": instance.title},
    )
