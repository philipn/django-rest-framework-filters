from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
import copy

from django.db import models
from django.db.models.constants import LOOKUP_SEP
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

            elif name not in new_class.declared_filters:
                new_class.base_filters[name] = new_class.fix_filter_field(filter_)

        return new_class


class FilterSet(six.with_metaclass(FilterSetMetaclass, filterset.FilterSet)):
    filter_overrides = {

        # In order to support ISO-8601 -- which is the default output for
        # DRF -- we need to use django-filter's IsoDateTimeFilter
        models.DateTimeField: {
            'filter_class': filters.IsoDateTimeFilter,
        },
    }
    _subset_cache = {}

    def __init__(self, *args, **kwargs):
        self._related_filterset_cache = kwargs.pop('cache', {})

        super(FilterSet, self).__init__(*args, **kwargs)

        for name, filter_ in six.iteritems(self.filters.copy()):
            if isinstance(filter_, filters.RelatedFilter):
                # Add an 'isnull' filter to allow checking if the relation is empty.
                filter_name = "%s%sisnull" % (filter_.name, LOOKUP_SEP)
                if filter_name not in self.filters:
                    self.filters[filter_name] = filters.BooleanFilter(name=filter_.name, lookup_type='isnull')

            elif isinstance(filter_, filters.MethodFilter):
                filter_.resolve_action()

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

            subset_class = related_filter.filterset.get_subset(rel_data)

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

        ex::

            # regular attribute filters
            name = FilterSet.get_filter_name('email')
            assert name == 'email'

            # exclusion filters
            name = FilterSet.get_filter_name('email!')
            assert name == 'email'

            # related filters
            name = FilterSet.get_filter_name('author__email')
            assert name == 'author'

        """
        # Attempt to match against filters with lookups first. (username__endswith)
        if param in cls.base_filters:
            return param

        # Attempt to match against exclusion filters
        if param[-1] == '!' and param[:-1] in cls.base_filters:
            return param[:-1]

        # Fallback to matching against relationships. (author__username__endswith).
        related_filters = [
            name for name, f in six.iteritems(cls.base_filters)
            if isinstance(f, filters.RelatedFilter)
        ]

        # preference more specific filters. eg, `note__author` over `note`.
        for name in sorted(related_filters)[::-1]:
            # we need to match against '__' to prevent eager matching against
            # like names. eg, note vs note2. Exact matches are handled above.
            if param.startswith("%s__" % name):
                return name

    @classmethod
    def get_subset(cls, params):
        """
        Returns a FilterSubset class that contains the subset of filters
        specified in the requested `params`. This is useful for creating
        FilterSets that traverse relationships, as it helps to minimize
        the deepcopy overhead incurred when instantiating the FilterSet.
        """
        # Determine names of filters from query params and remove empty values.
        # param names that traverse relations are translated to just the local
        # filter names. eg, `author__username` => `author`. Empty values are
        # removed, as they indicate an unknown field eg, author__foobar__isnull
        filter_names = [cls.get_filter_name(param) for param in params]
        filter_names = [f for f in filter_names if f is not None]

        # attempt to retrieve related filterset subset from the cache
        key = cls.cache_key(filter_names)
        subset_class = cls.cache_get(key)

        # if no cached subset, then derive base_filters and create new subset
        if subset_class is not None:
            return subset_class

        class FilterSubsetMetaclass(FilterSetMetaclass):
            def __new__(cls, name, bases, attrs):
                new_class = super(FilterSubsetMetaclass, cls).__new__(cls, name, bases, attrs)
                new_class.base_filters = OrderedDict([
                    (name, f)
                    for name, f in six.iteritems(new_class.base_filters)
                    if name in filter_names
                ])
                return new_class

        class FilterSubset(six.with_metaclass(FilterSubsetMetaclass, cls)):
            pass

        FilterSubset.__name__ = str('%sSubset' % (cls.__name__, ))
        cls.cache_set(key, FilterSubset)
        return FilterSubset

    @classmethod
    def cache_key(cls, filter_names):
        return '%sSubset-%s' % (cls.__name__, '-'.join(sorted(filter_names)), )

    @classmethod
    def cache_get(cls, key):
        return cls._subset_cache.get(key)

    @classmethod
    def cache_set(cls, key, value):
        cls._subset_cache[key] = value

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
            return filters.BooleanFilter(name=f.name, lookup_type='isnull')
        if lookup_type == 'in' and type(f) == filters.NumberFilter:
            return filters.InSetNumberFilter(name=f.name, lookup_type='in')
        if lookup_type == 'in' and type(f) == filters.CharFilter:
            return filters.InSetCharFilter(name=f.name, lookup_type='in')
        return f
