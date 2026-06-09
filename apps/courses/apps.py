from django.apps import AppConfig


class CoursesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.courses"
    label = "courses"

    def ready(self):
        # Register post_save signal handlers for audit logging
        import apps.courses.signals  # noqa: F401
