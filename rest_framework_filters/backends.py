
from django.template import loader
from rest_framework import compat
import rest_framework.filters

from .filterset import FilterSet


class DjangoFilterBackend(rest_framework.filters.DjangoFilterBackend):
    default_filter_set = FilterSet

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            if hasattr(filter_class, 'get_subset'):
                filter_class = filter_class.get_subset(request.query_params)
            return filter_class(request.query_params, queryset=queryset).qs

        return queryset

    def to_html(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)
        if not filter_class:
            return None
        filter_instance = filter_class(request.query_params, queryset=queryset)

        # forces `form` evaluation before `qs` is called. This prevents an empty form from being cached.
        filter_instance.form

        context = {
            'filter': filter_instance
        }
        template = loader.get_template(self.template)
        return compat.template_render(template, context)
