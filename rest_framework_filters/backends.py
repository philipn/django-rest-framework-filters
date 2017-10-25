from contextlib import contextmanager

from django.http import QueryDict
from django_filters.rest_framework import backends
from rest_framework.exceptions import ValidationError
from rest_framework.request import clone_request

from .complex_ops import decode_querystring_ops, OPERATORS
from .filterset import FilterSet


@contextmanager
def noop(self):
    yield


class DjangoFilterBackend(backends.DjangoFilterBackend):
    default_filter_set = FilterSet

    @contextmanager
    def patch_for_rendering(self, request):
        """
        Patch `get_filter_class()` so the resulting filterset does not perform
        filter expansion during form rendering.
        """
        original = self.get_filter_class

        def get_filter_class(view, queryset=None):
            filter_class = original(view, queryset)
            filter_class.requested_filters = noop

            return filter_class

        self.get_filter_class = get_filter_class
        yield
        self.get_filter_class = original

    def to_html(self, request, queryset, view):
        # patching the behavior of `get_filter_class()` in this method allows
        # us to avoid maintenance issues with code duplication.
        with self.patch_for_rendering(request):
            return super(DjangoFilterBackend, self).to_html(request, queryset, view)


class ComplexFilterBackend(DjangoFilterBackend):
    complex_filter_param = 'filters'

    def filter_queryset(self, request, original, view):
        parent = super(ComplexFilterBackend, self)

        if self.complex_filter_param not in request.query_params:
            return parent.filter_queryset(request, original, view)

        encoded_querystring = request.query_params[self.complex_filter_param]
        try:
            querystring_ops = decode_querystring_ops(encoded_querystring)
        except ValidationError as exc:
            raise ValidationError({self.complex_filter_param: exc.detail})

        queryset = original
        queryset_op = OPERATORS['&']  # effectively a noop

        for querystring, op in querystring_ops:
            cloned = clone_request(request, request.method)
            cloned._request.GET = QueryDict(querystring)

            queryset = queryset_op(queryset, parent.filter_queryset(cloned, original, view))
            queryset_op = OPERATORS.get(op)

        return queryset
