from __future__ import absolute_import
from __future__ import unicode_literals

from copy import copy

try:
    from django.db.models.constants import LOOKUP_SEP
except ImportError:  # pragma: nocover
    # Django < 1.5 fallback
    from django.db.models.sql.constants import LOOKUP_SEP  # noqa
from django.db import models
from django.utils.datastructures import SortedDict
from django.db.models.related import RelatedObject
from django.utils import six

import django_filters
import django_filters.filters
from django_filters.filterset import get_model_field

from . import filters


class FilterSet(django_filters.FilterSet):
    # In order to support ISO-8601 -- which is the default output for
    # DRF -- we need to set up custom date/time input formats.
    filter_overrides = {
        models.DateTimeField: {
            'filter_class': filters.DateTimeFilter,
        }, 
        models.DateField: {
            'filter_class': filters.DateFilter,
        }, 
        models.TimeField: {
            'filter_class': filters.TimeFilter,
        },
    }

    LOOKUP_TYPES = django_filters.filters.LOOKUP_TYPES

    def __init__(self, *args, **kwargs):
        super(FilterSet, self).__init__(*args, **kwargs)

        for name, filter_ in six.iteritems(self.filters):
            if isinstance(filter_, filters.RelatedFilter):
                # Populate our FilterSet fields with the fields we've stored
                # in RelatedFilter.
                filter_.setup_filterset()
                self.populate_from_filterset(filter_.filterset, filter_, name)
                # Add an 'isnull' filter to allow checking if the relation is empty.
                isnull_filter = filters.BooleanFilter(name=("%s%sisnull" % (filter_.name, LOOKUP_SEP)))
                self.filters['%s%s%s' % (filter_.name, LOOKUP_SEP, 'isnull')] = isnull_filter
            elif isinstance(filter_, filters.AllLookupsFilter):
                # Populate our FilterSet fields with all the possible
                # filters for the AllLookupsFilter field.
                model = self._meta.model
                field = get_model_field(model, filter_.name)
                for lookup_type in self.LOOKUP_TYPES:
                    if isinstance(field, RelatedObject):
                        f = self.filter_for_reverse_field(field, filter_.name)
                    else:
                        f = self.filter_for_field(field, filter_.name)
                    f.lookup_type = lookup_type
                    f = self.fix_filter_field(f)
                    self.filters["%s%s%s" % (name, LOOKUP_SEP, lookup_type)] = f

    def fix_filter_field(self, f):
        """
        Fix the filter field based on the lookup type. 
        """
        lookup_type = f.lookup_type
        if lookup_type == 'isnull':
            return filters.BooleanFilter(name=("%s%sisnull" % (f.name, LOOKUP_SEP)))
        return f

    def populate_from_filterset(self, filterset, filter_, name):
        """
        Populate `filters` with filters provided on `filterset`.
        """
        def _should_skip():
            for name, filter_ in six.iteritems(self.filters):
                if filter_value == filter_:
                    return True
                # Avoid infinite recursion on recursive relations.  If the queryset and
                # class are the same, then we assume that we've already added this
                # filter previously along the lookup chain, e.g.
                # a__b__a <-- the last 'a' there.
                if (isinstance(filter_, filters.RelatedFilter) and
                    isinstance(filter_value, filters.RelatedFilter)):
                    if filter_value.extra.get('queryset', None) == filter_.extra.get('queryset'):
                        return True
            return False

        for (filter_key, filter_value) in filterset.base_filters.items():
            if _should_skip():
                continue

            filter_value = copy(filter_value)

            # Guess on the field to join on, if applicable
            if not getattr(filter_value, 'parent_relation', None):
                filter_value.parent_relation = filterset._meta.model.__name__.lower()

            # We use filter_.name -- which is the internal name, to do the actual query
            filter_name = filter_value.name
            filter_value.name = '%s%s%s' % (filter_.name, LOOKUP_SEP, filter_name)
            # and then we use the /given/ name keyword as the actual querystring lookup, and
            # the filter's name in the related class (filter_key).
            self.filters['%s%s%s' % (name, LOOKUP_SEP, filter_key)] = filter_value
