from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.courses.ui_views import CourseCreatePageView
from apps.location.ui_views import CitySelectorView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/location/", include("apps.location.urls")),
    path("api/courses/", include("apps.courses.urls")),
    path("api/enrollments/", include("apps.enrollments.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("courses/create/", CourseCreatePageView.as_view(), name="course-create-page"),
    path("location/select/", CitySelectorView.as_view(), name="city-selector"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
