from copy import deepcopy

import rest_framework.filters
from rest_framework.compat import django_filters

from .filterset import FilterSet



class DjangoFilterBackend(rest_framework.filters.DjangoFilterBackend):
    """
    A version of `DjangoFilterBackend` that caches repeated filter classes
    and uses our FilterSet by default.
    """
    default_filter_set = FilterSet

    _filter_instance_cache = {}

    def _setup_filter_instance(self, _filter, query_params, queryset=None):
        _filter.data = query_params or {}
        _filter.is_bound = query_params is not None

        if hasattr(_filter, '_qs'):
            del _filter._qs
        if hasattr(_filter, '_form'):
            del _filter._form
        if hasattr(_filter, '_ordering_field'):
            del _filter._ordering_field

        if queryset is None:
            queryset = _filter._meta.model._default_manager.all()
        _filter.queryset = queryset
        # propagate the model being used through the filters
        for f in _filter.filters.values():
            f.model = _filter._meta.model

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class:
            if filter_class in self._filter_instance_cache:
                _filter = self._filter_instance_cache[filter_class]
                self._setup_filter_instance(_filter, request.QUERY_PARAMS, queryset=queryset)
            else:
                _filter = filter_class(request.QUERY_PARAMS, queryset=queryset)
                self._filter_instance_cache[filter_class] = _filter

            return _filter.qs

        return queryset
