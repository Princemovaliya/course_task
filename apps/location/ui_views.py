from django.views.generic import TemplateView


class CitySelectorView(TemplateView):
    template_name = "city_selector.html"
