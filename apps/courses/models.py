import uuid

from django.conf import settings
from django.db import models


class Course(models.Model):
    """
    A course offered by an instructor at a specific location and time window.

    Location fields store ISO codes / city name as strings (validated via Location API).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="courses",
      
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    max_capacity = models.PositiveIntegerField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    # Embedded location — not FK; validated against external Location API on write
    country = models.CharField(max_length=10)
    state = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    # Soft-close flag: inactive courses are hidden from student browse lists
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses"
        ordering = ["-start_datetime"]

    def __str__(self):
        return self.title
