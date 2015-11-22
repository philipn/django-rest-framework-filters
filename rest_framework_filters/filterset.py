from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
import copy

from django.db.models.constants import LOOKUP_SEP
from django.db import models
try:
    from django.db.models.related import RelatedObject as ForeignObjectRel
except ImportError:  # pragma: nocover
    # Django >= 1.8 replaces RelatedObject with ForeignObjectRel
    from django.db.models.fields.related import ForeignObjectRel
from django.utils import six

import django_filters
import django_filters.filters
from django_filters import filterset

from . import filters


class FilterSetMetaclass(filterset.FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)

        # Populate our FilterSet fields with all the possible
        # filters for the AllLookupsFilter field.
        for name, filter_ in six.iteritems(new_class.base_filters.copy()):
            if isinstance(filter_, filters.AllLookupsFilter):
                model = new_class._meta.model
                field = filterset.get_model_field(model, filter_.name)

                for lookup_type in django_filters.filters.LOOKUP_TYPES:
                    if isinstance(field, ForeignObjectRel):
                        f = new_class.filter_for_reverse_field(field, filter_.name)
                    else:
                        f = new_class.filter_for_field(field, filter_.name)
                    f.lookup_type = lookup_type
                    f = new_class.fix_filter_field(f)

                    # compute filter name
                    filter_name = name
                    # Don't add "exact" to filter names
                    if lookup_type != 'exact':
                        filter_name = LOOKUP_SEP.join([name, lookup_type])

                    new_class.base_filters[filter_name] = f

        return new_class


class FilterSet(six.with_metaclass(FilterSetMetaclass, filterset.FilterSet)):
    filter_overrides = {

        # In order to support ISO-8601 -- which is the default output for
        # DRF -- we need to use django-filter's IsoDateTimeFilter
        models.DateTimeField: {
            'filter_class': filters.IsoDateTimeFilter,
        },
    }

    def __init__(self, *args, **kwargs):
        self._related_filterset_cache = kwargs.pop('cache', {})

        super(FilterSet, self).__init__(*args, **kwargs)

        for name, filter_ in six.iteritems(self.filters.copy()):
            if isinstance(filter_, filters.RelatedFilter):
                filter_.setup_filterset()

                # Add an 'isnull' filter to allow checking if the relation is empty.
                isnull = "%s%sisnull" % (filter_.name, LOOKUP_SEP)
                if isnull not in self.filters:
                    self.filters[isnull] = filters.BooleanFilter(name=isnull)

    def get_filters(self):
        """
        Build a set of filters based on the requested data. The resulting set
        will walk `RelatedFilter`s to recursively build the set of filters.
        """
        requested_filters = OrderedDict()

        # Add plain lookup filters if match. ie, `username__icontains`
        for filter_key, filter_value in six.iteritems(self.filters):
            exclude_key = '%s!' % filter_key

            if filter_key in self.data:
                requested_filters[filter_key] = filter_value

            if exclude_key in self.data:
                filter_value = copy.deepcopy(filter_value)
                filter_value.exclude = not filter_value.exclude
                requested_filters[exclude_key] = filter_value

        # build a map of potential {rel: {filter: value}} data
        related_data = OrderedDict()
        for filter_key, value in six.iteritems(self.data):
            if filter_key not in self.filters:

                # skip non lookup/related keys
                if LOOKUP_SEP not in filter_key:
                    continue

                rel_name, filter_key = filter_key.split(LOOKUP_SEP, 1)

                related_data.setdefault(rel_name, OrderedDict())
                related_data[rel_name][filter_key] = value

        # walk the related lookup data. If the filter is a RelatedFilter,
        # then instantiate its filterset and append its filters.
        for rel_name, rel_data in related_data.items():
            related_filter = self.filters.get(rel_name, None)

            # skip non-`RelatedFilter`s
            if not isinstance(related_filter, filters.RelatedFilter):
                continue

            # get known filter names
            filterset_class = related_filter.filterset
            filter_names = [filterset_class.get_filter_name(param) for param in rel_data.keys()]

            # attempt to retrieve related filterset subset from the cache
            key = self.cache_key(filterset_class, filter_names)
            subset_class = self.cache_get(key)

            # otherwise build and insert it into the cache
            if subset_class is None:
                subset_class = related_filter.get_filterset_subset(filter_names)
                self.cache_set(key, subset_class)

            # initialize and copy filters
            filterset = subset_class(data=rel_data)
            rel_filters = filterset.get_filters()
            for filter_key, filter_value in six.iteritems(rel_filters):
                # modify filter name to account for relationship
                rel_filter_key = LOOKUP_SEP.join([rel_name, filter_key])
                filter_value.name = LOOKUP_SEP.join([related_filter.name, filter_value.name])
                requested_filters[rel_filter_key] = filter_value

        return requested_filters

    @classmethod
    def get_filter_name(cls, param):
        """
        Get the filter name for the request data parameter.
        """
        # Attempt to match against filters with lookups first. (username__endswith)
        if param in cls.base_filters:
            return param

        # Attempt to match against exclusion filters
        if param[-1] == '!' and param[:-1] in cls.base_filters:
            return param[:-1]

        # Fallback to matching against relationships. (author__username__endswith)
        related_param = param.split(LOOKUP_SEP, 1)[0]
        f = cls.base_filters.get(related_param, None)
        if isinstance(f, filters.RelatedFilter):
            return related_param

    def cache_key(self, filterset, filter_names):
        return '%sSubset-%s' % (filterset.__name__, '-'.join(sorted(filter_names)), )

    def cache_get(self, key):
        return self._related_filterset_cache.get(key)

    def cache_set(self, key, value):
        self._related_filterset_cache[key] = value

    @property
    def qs(self):
        available_filters = self.filters
        requested_filters = self.get_filters()

        self.filters = requested_filters
        qs = super(FilterSet, self).qs
        self.filters = available_filters

        return qs

    @classmethod
    def fix_filter_field(cls, f):
        """
        Fix the filter field based on the lookup type.
        """
        lookup_type = f.lookup_type
        if lookup_type == 'isnull':
            return filters.BooleanFilter(name=("%s%sisnull" % (f.name, LOOKUP_SEP)))
        if lookup_type == 'in' and type(f) == filters.NumberFilter:
            return filters.InSetNumberFilter(name=("%s%sin" % (f.name, LOOKUP_SEP)))
        if lookup_type == 'in' and type(f) == filters.CharFilter:
            return filters.InSetCharFilter(name=("%s%sin" % (f.name, LOOKUP_SEP)))
        return f
