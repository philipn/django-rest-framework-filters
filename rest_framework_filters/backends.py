
from contextlib import contextmanager
from django_filters.rest_framework import backends

from .filterset import FilterSet


class DjangoFilterBackend(backends.DjangoFilterBackend):
    default_filter_set = FilterSet

    @contextmanager
    def patched_filter_class(self, request):
        """
        Patch `get_filter_class()` to get the subset based on the request params
        """
        original = self.get_filter_class

        def get_subset_class(view, queryset=None):
            filter_class = original(view, queryset)

            if filter_class and hasattr(filter_class, 'get_subset'):
                filter_class = filter_class.get_subset(request.query_params)

            return filter_class

        self.get_filter_class = get_subset_class
        yield
        self.get_filter_class = original

    def filter_queryset(self, request, queryset, view):
        # patching the behavior of `get_filter_class()` in this method allows
        # us to avoid maintenance issues with code duplication.
        with self.patched_filter_class(request):
            return super(DjangoFilterBackend, self).filter_queryset(request, queryset, view)
