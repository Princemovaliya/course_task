from django.views.generic import TemplateView


class CourseCreatePageView(TemplateView):
    template_name = "course_create.html"
