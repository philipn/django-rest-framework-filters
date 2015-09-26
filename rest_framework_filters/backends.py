
import rest_framework.filters
from .filterset import FilterSet


class DjangoFilterBackend(rest_framework.filters.DjangoFilterBackend):
    default_filter_set = FilterSet
