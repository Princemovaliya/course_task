from django.contrib import admin

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "enrolled_at", "cancelled_at")
    list_filter = ("status",)
    search_fields = ("student__email", "course__title")
