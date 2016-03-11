from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
import copy
import warnings

from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related import ForeignObjectRel
from django.utils import six
from django.forms import CharField, Select
from django.core.exceptions import FieldError, ValidationError

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

    @property
    def related_filters(self):
        # check __dict__ instead of use hasattr. we *don't* want to check
        # parents for existence of existing cache. eg, we do not want
        # FilterSet.get_subset([...]) to return the same cache.
        if '_related_filters' not in self.__dict__:
            self._related_filters = OrderedDict([
                (name, f) for name, f in six.iteritems(self.base_filters)
                if isinstance(f, filters.RelatedFilter)
            ])
        return self._related_filters


class FilterSet(six.with_metaclass(FilterSetMetaclass, filterset.FilterSet)):
    filter_overrides = {
        models.BooleanField: {
            'filter_class': filters.BooleanFilter,
        },

        # In order to support ISO-8601 -- which is the default output for
        # DRF -- we need to use django-filter's IsoDateTimeFilter
        models.DateTimeField: {
            'filter_class': filters.IsoDateTimeFilter,
        },
    }
    _subset_cache = {}

    def __init__(self, *args, **kwargs):
        if 'cache' in kwargs:
            warnings.warn(
                "'cache' argument is deprecated. Override '_subset_cache' instead.",
                DeprecationWarning, stacklevel=2
            )
            self.__class__._subset_cache = kwargs.pop('cache', None)

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
        # build param data for related filters: {rel: {param: value}}
        related_data = OrderedDict(
            [(name, OrderedDict()) for name in self.__class__.related_filters]
        )
        for param, value in six.iteritems(self.data):
            filter_name, related_param = self.get_related_filter_param(param)

            # skip non lookup/related keys
            if filter_name is None:
                continue

            if filter_name in related_data:
                related_data[filter_name][related_param] = value

        # build the compiled set of all filters
        requested_filters = OrderedDict()
        for filter_name, f in six.iteritems(self.filters):
            exclude_name = '%s!' % filter_name

            # Add plain lookup filters if match. ie, `username__icontains`
            if filter_name in self.data:
                requested_filters[filter_name] = f

            # include exclusion keys
            if exclude_name in self.data:
                f = copy.deepcopy(f)
                f.exclude = not f.exclude
                requested_filters[exclude_name] = f

            # include filters from related subsets
            if isinstance(f, filters.RelatedFilter) and filter_name in related_data:
                subset_data = related_data[filter_name]
                subset_class = f.filterset.get_subset(subset_data)
                filterset = subset_class(data=subset_data)

                # modify filter names to account for relationship
                for related_name, related_f in six.iteritems(filterset.get_filters()):
                    related_name = LOOKUP_SEP.join([filter_name, related_name])
                    related_f.name = LOOKUP_SEP.join([f.name, related_f.name])
                    requested_filters[related_name] = related_f

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
        related_filters = cls.related_filters.keys()

        # preference more specific filters. eg, `note__author` over `note`.
        for name in sorted(related_filters)[::-1]:
            # we need to match against '__' to prevent eager matching against
            # like names. eg, note vs note2. Exact matches are handled above.
            if param.startswith("%s%s" % (name, LOOKUP_SEP)):
                return name

    @classmethod
    def get_related_filter_param(cls, param):
        """
        Get a tuple of (filter name, related param).

        ex::

            name, param = FilterSet.get_filter_name('author__email__foobar')
            assert name == 'author'
            assert param = 'email__foobar'

            name, param = FilterSet.get_filter_name('author')
            assert name is None
            assert param is None

        """
        related_filters = cls.related_filters.keys()

        # preference more specific filters. eg, `note__author` over `note`.
        for name in sorted(related_filters)[::-1]:
            # we need to match against '__' to prevent eager matching against
            # like names. eg, note vs note2. Exact matches are handled above.
            if param.startswith("%s%s" % (name, LOOKUP_SEP)):
                # strip param + LOOKUP_SET from param
                related_param = param[len(name) + len(LOOKUP_SEP):]
                return name, related_param

        # not a related param
        return None, None

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

    def get_ordering_field(self):
        """
        Fixed get_ordering_field to not depend on self.filters because we
        overwrite them when accessing self.qs.
        """
        ordering_field = super(FilterSet, self).get_ordering_field()
        if self._meta.order_by is True:
            if getattr(self, "default_order", None):
                choices = [(",".join(self.default_order),) * 2]
            else:
                choices = []
            for field in self._meta.model._meta.get_fields():  # pylint: disable=protected-access
                label = getattr(field, "verbose_name", field.name.capitalize())
                choices += [
                    (field.name, label),
                    ("-{}".format(field.name), "{} (descending)".format(label))
                ]

            def validator_factory(queryset):
                def validate_order_by(value):
                    ordered_queryset = queryset.order_by(*value.split(","))
                    compiler = ordered_queryset.query.get_compiler(using=ordered_queryset.db)
                    try:
                        compiler.get_order_by()
                    except FieldError:
                        raise ValidationError("'{}' is not a valid order".format(value))
                return validate_order_by

            ordering_field = CharField(
                label=ordering_field.label,
                required=False,
                widget=Select,
                validators=[validator_factory(self.queryset)])
            ordering_field.choices = choices
            ordering_field.widget.choices = choices
        return ordering_field

    def get_order_by(self, order_value):
        return order_value.split(",")
