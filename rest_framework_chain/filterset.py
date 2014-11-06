from copy import copy

try:
    from django.db.models.constants import LOOKUP_SEP
except ImportError:  # pragma: nocover
    # Django < 1.5 fallback
    from django.db.models.sql.constants import LOOKUP_SEP  # noqa
from django.utils.datastructures import SortedDict
from django.db.models.related import RelatedObject
from django.utils import six

import django_filters
from django_filters.filters import LOOKUP_TYPES
from django_filters.filterset import get_model_field

from .filters import RelatedFilter, AllLookupsFilter

def populate_from_filterset(filterset, name, parent_filter, filters):
    """
    Populate `filters` with filters provided on `filterset`.
    """
    def _should_skip():
        for name, filter_ in six.iteritems(filters):
            if f == filter_:
                return True
            # Avoid infinite recursion on recursive relations.  If the queryset and
            # class are the same, then we assume that we've already added this
            # filter previously along the lookup chain, e.g.
            # a__b__a <-- the last 'a' there.
            if isinstance(filter_, RelatedFilter) and isinstance(f, RelatedFilter):
                if f.extra.get('queryset', None) == filter_.extra.get('queryset'):
                    return True
        return False

    for f in filterset.base_filters.values():
        if _should_skip():
            continue

        f = copy(f)
        old_field_name = f.name
        f.name = '%s%s%s' % (parent_filter.name, LOOKUP_SEP, f.name)
        filters['%s%s%s' % (name, LOOKUP_SEP, old_field_name)] = f

class ChainedFilterSet(django_filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super(ChainedFilterSet, self).__init__(*args, **kwargs)

        for name, filter_ in six.iteritems(self.filters):
            if isinstance(filter_, RelatedFilter):
                # Populate our FilterSet fields with the fields we've stored
                # in RelatedFilter.
                filter_.setup_filterset()
                populate_from_filterset(filter_.filterset, name, filter_, self.filters)
            elif isinstance(filter_, AllLookupsFilter):
                # Populate our FilterSet fields with all the possible
                # filters for the AllLookupsFilter field.
                model = self._meta.model
                field = get_model_field(model, filter_.name)
                for lookup_type in LOOKUP_TYPES:
                    if isinstance(field, RelatedObject):
                        f = self.filter_for_reverse_field(field, filter_.name)
                    else:
                        f = self.filter_for_field(field, filter_.name)
                    f.lookup_type = lookup_type
                    self.filters["%s__%s" % (name, lookup_type)] = f
