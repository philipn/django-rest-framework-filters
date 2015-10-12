
import rest_framework.filters
from .filterset import FilterSet


class DjangoFilterBackend(rest_framework.filters.DjangoFilterBackend):
    default_filter_set = FilterSet
    _related_filterset_cache = {}  # set to None to disable cache propagation

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            cache = self._related_filterset_cache
            return filter_class(request.query_params, queryset=queryset, cache=cache).qs

        return queryset
