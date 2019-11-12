import warnings
from contextlib import contextmanager
from django_filters.rest_framework import backends

from django_filters import compat
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

    def get_schema_fields(self, view):
        # Use the filter_class expanded filters property instead of
        # base filters so that the nested related filter can be included
        assert compat.coreapi is not None, 'coreapi must be installed to use `get_schema_fields()`'
        assert compat.coreschema is not None, 'coreschema must be installed to use `get_schema_fields()`'

        filter_class = getattr(view, 'filter_class', None)
        if filter_class is None:
            try:
                filter_class = self.get_filter_class(view, view.get_queryset())
            except Exception:
                warnings.warn(
                    "{} is not compatible with schema generation".format(view.__class__)
                )
                filter_class = None

        return [] if not filter_class else [
            compat.coreapi.Field(
                name=field_name,
                required=field.extra['required'],
                location='query',
                schema=self.get_coreschema_field(field)
                # expanded_filters in place of base_filters
            ) for field_name, field in filter_class.expanded_filters.items()
        ]

