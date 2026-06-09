from .models import AuditLog


def log_event(actor, action, target, metadata=None):
    """
    Central helper for writing audit trail entries.

    Called from Django signals (course events) and views (enrollment events in Phase 4).
    """
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target.__class__.__name__,
        target_id=target.pk,
        metadata=metadata or {"title": str(target)},
    )
