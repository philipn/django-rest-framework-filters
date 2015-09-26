from __future__ import absolute_import
from __future__ import unicode_literals

from copy import copy
from collections import OrderedDict

try:
    from django.db.models.constants import LOOKUP_SEP
except ImportError:  # pragma: nocover
    # Django < 1.5 fallback
    from django.db.models.sql.constants import LOOKUP_SEP  # noqa
from django.db import models
try:
    from django.db.models.related import RelatedObject as ForeignObjectRel
except ImportError:  # pragma: nocover
    # Django >= 1.8 replaces RelatedObject with ForeignObjectRel
    from django.db.models.fields.related import ForeignObjectRel
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
                filter_.setup_filterset()

                # Add an 'isnull' filter to allow checking if the relation is empty.
                isnull_filter = filters.BooleanFilter(name=("%s%sisnull" % (filter_.name, LOOKUP_SEP)))
                self.filters['%s%s%s' % (filter_.name, LOOKUP_SEP, 'isnull')] = isnull_filter

            elif isinstance(filter_, filters.AllLookupsFilter):
                # Populate our FilterSet fields with all the possible
                # filters for the AllLookupsFilter field.
                model = self._meta.model
                field = get_model_field(model, filter_.name)
                for lookup_type in self.LOOKUP_TYPES:
                    if isinstance(field, ForeignObjectRel):
                        f = self.filter_for_reverse_field(field, filter_.name)
                    else:
                        f = self.filter_for_field(field, filter_.name)
                    f.lookup_type = lookup_type
                    f = self.fix_filter_field(f)
                    self.filters["%s%s%s" % (name, LOOKUP_SEP, lookup_type)] = f

    def get_filters(self):
        """
        Build a set of filters based on the requested data. The resulting set
        will walk `RelatedFilter`s to recursively build the set of filters.
        """
        requested_filters = OrderedDict()

        # filter out any filters not included in the request data
        for filter_key, filter_value in six.iteritems(self.filters):
            if filter_key in self.data:
                requested_filters[filter_key] = filter_value

        # build a map of potential {rel: [filter]} pairs
        related_data = OrderedDict()
        for filter_key in self.data:
            if filter_key not in self.filters:

                # skip non lookup/related keys
                if LOOKUP_SEP not in filter_key:
                    continue

                rel_name, filter_key = filter_key.split(LOOKUP_SEP, 1)

                related_data.setdefault(rel_name, [])
                related_data[rel_name].append(filter_key)

        # walk the related lookup data. If the rel is a RelatedFilter,
        # then instantiate its filterset and append its filters
        for rel_name, rel_data in related_data.items():
            related_filter = self.filters.get(rel_name, None)

            # skip non-`RelatedFilter`s
            if not isinstance(related_filter, filters.RelatedFilter):
                continue

            filterset = related_filter.filterset(data=rel_data)
            rel_filters = filterset.get_filters()

            for filter_key, filter_value in six.iteritems(rel_filters):
                rel_filter_key = LOOKUP_SEP.join([rel_name, filter_key])
                filter_value.name = LOOKUP_SEP.join([related_filter.name, filter_value.name])
                requested_filters[rel_filter_key] = filter_value

        return requested_filters

    @property
    def qs(self):
        available_filters = self.filters
        requested_filters = self.get_filters()

        self.filters = requested_filters
        qs = super(FilterSet, self).qs
        self.filters = available_filters

        return qs

    def fix_filter_field(self, f):
        """
        Fix the filter field based on the lookup type. 
        """
        lookup_type = f.lookup_type
        if lookup_type == 'isnull':
            return filters.BooleanFilter(name=("%s%sisnull" % (f.name, LOOKUP_SEP)))
        if lookup_type == 'in' and type(f) in [filters.NumberFilter]:
            return filters.InSetNumberFilter(name=("%s%sin" % (f.name, LOOKUP_SEP)))
        return f
