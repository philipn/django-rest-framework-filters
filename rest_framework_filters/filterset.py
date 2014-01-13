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
from django_filters.filters import LOOKUP_TYPES
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

    def __init__(self, *args, **kwargs):
        super(FilterSet, self).__init__(*args, **kwargs)

        for name, filter_ in six.iteritems(self.filters):
            if isinstance(filter_, filters.RelatedFilter):
                # Populate our FilterSet fields with the fields we've stored
                # in RelatedFilter.
                filter_.setup_filterset()
                self.populate_from_filterset(filter_.filterset, name)
            elif isinstance(filter_, filters.AllLookupsFilter):
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
                    self.filters["%s__%s" % (filter_.name, lookup_type)] = f

    def populate_from_filterset(self, filterset, name):
        """
        Populate `filters` with filters provided on `filterset`.
        """
        def _should_skip():
            for name, filter_ in six.iteritems(self.filters):
                if f == filter_:
                    return True
                # Avoid infinite recursion on recursive relations.  If the queryset and
                # class are the same, then we assume that we've already added this
                # filter previously along the lookup chain, e.g.
                # a__b__a <-- the last 'a' there.
                if (isinstance(filter_, filters.RelatedFilter) and
                    isinstance(f, filters.RelatedFilter)):
                    if f.extra.get('queryset', None) == filter_.extra.get('queryset'):
                        return True
            return False
    
        for f in filterset.base_filters.values():
            if _should_skip():
                continue
    
            f = copy(f)
            f.name = '%s%s%s' % (name, LOOKUP_SEP, f.name)
            self.filters[f.name] = f
