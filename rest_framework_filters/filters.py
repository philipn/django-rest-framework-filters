import warnings

from django_filters.rest_framework.filters import *  # noqa
from django_filters.rest_framework.filters import Filter, ModelChoiceFilter

from rest_framework_filters.utils import import_class, relative_class_path

ALL_LOOKUPS = '__all__'


class AutoFilter(Filter):
    """
    Declarative alternative to using the `Meta.fields` dictionary syntax. These
    fields are processed by the metaclass and resolved into per-lookup filters.

    `AutoFilter`s benefit from their declarative nature in that it is possible
    to change the parameter name of the generated filters. This is not possible
    with the `Meta.fields` syntax.
    """

    def __init__(self, *args, lookups=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookups = lookups or []


class RelatedFilter(AutoFilter, ModelChoiceFilter):
    """
    A `ModelChoiceFilter` that defines a relationship to another `FilterSet`.
    This related filterset is processed by the filter's `parent` instance, and
    """

    def __init__(self, filterset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filterset = filterset

    def filterset():
        def fget(self):
            if isinstance(self._filterset, str):
                path = relative_class_path(self.parent, self._filterset)
                self._filterset = import_class(path)
            return self._filterset

        def fset(self, value):
            self._filterset = value

        return locals()
    filterset = property(**filterset())

    def get_queryset(self, request):
        queryset = super(RelatedFilter, self).get_queryset(request)
        assert queryset is not None, \
            "Expected `.get_queryset()` for related filter '%s.%s' to return a `QuerySet`, but got `None`." \
            % (self.parent.__class__.__name__, self.field_name)
        return queryset


class AllLookupsFilter(AutoFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lookups=ALL_LOOKUPS, **kwargs)
        warnings.warn(
            "`AllLookupsFilter()` has been deprecated in favor of `AutoFilter(lookups='__all__')`.",
            DeprecationWarning, stacklevel=2)
