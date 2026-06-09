from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for admin audit trail review."""

    actor_email = serializers.EmailField(source="actor.email", read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "actor_email",
            "action",
            "target_type",
            "target_id",
            "metadata",
            "timestamp",
        )
        read_only_fields = fields
