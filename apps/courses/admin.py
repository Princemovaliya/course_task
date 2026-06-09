from django.contrib import admin

from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "city", "start_datetime", "is_active")
    list_filter = ("is_active", "country", "state")
    search_fields = ("title", "instructor__email", "city")
    readonly_fields = ("id", "created_at", "updated_at")
