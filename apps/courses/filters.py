import django_filters

from .models import Course


class CourseFilter(django_filters.FilterSet):
    """Query-param filters for student course browse (GET /api/courses/)."""

    country = django_filters.CharFilter(field_name="country", lookup_expr="iexact")
    state = django_filters.CharFilter(field_name="state", lookup_expr="iexact")
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    # Filter courses starting on or after the given datetime
    start_datetime = django_filters.DateTimeFilter(
        field_name="start_datetime",
        lookup_expr="gte",
    )

    class Meta:
        model = Course
        fields = ["country", "state", "city", "start_datetime"]
