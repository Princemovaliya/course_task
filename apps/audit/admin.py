from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    # Audit logs are append-only — never editable from admin
    list_display = ("action", "actor", "target_type", "target_id", "timestamp")
    list_filter = ("action", "target_type")
    search_fields = ("actor__email", "target_id")
    readonly_fields = (
        "id",
        "actor",
        "action",
        "target_type",
        "target_id",
        "metadata",
        "timestamp",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
