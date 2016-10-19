from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
import copy
import warnings

from django.db.models.constants import LOOKUP_SEP
from django.utils import six

from django_filters import filterset, rest_framework
from django_filters.utils import get_model_field

from . import filters
from . import utils


def _base(f):
    f._base = True
    return f


def _get_fix_filter_field(cls):
    method = getattr(cls, 'fix_filter_field')
    if not getattr(method, '_base', False):
        warnings.warn(
            'fix_filter_field is deprecated and no longer necessary. See: '
            'https://github.com/philipn/django-rest-framework-filters/issues/62',
            DeprecationWarning, stacklevel=2
        )
    return cls.fix_filter_field


class FilterSetMetaclass(filterset.FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)
        fix_filter_field = _get_fix_filter_field(new_class)
        opts = copy.deepcopy(new_class._meta)

        # order_by is not compatible.
        if opts.order_by:
            opts.order_by = False
            warnings.warn(
                'order_by is no longer supported. Use '
                'rest_framework.filters.OrderingFilter instead. See: '
                'https://github.com/philipn/django-rest-framework-filters/issues/72',
                DeprecationWarning, stacklevel=2
            )

        # If no model is defined, skip all lookups processing
        if not opts.model:
            return new_class

        # Determine declared filters and filters to generate lookups from. Declared
        # filters have precedence over generated filters and should not be overwritten.
        declared_filters, lookups_filters = OrderedDict(), OrderedDict()
        for name, f in six.iteritems(new_class.declared_filters):
            if isinstance(f, (filters.AllLookupsFilter, filters.RelatedFilter)):
                lookups_filters[name] = f

            # `AllLookupsFilter` is an exception, as it should be overwritten
            if not isinstance(f, filters.AllLookupsFilter):
                declared_filters[name] = f

        # generate filters for AllLookups/Related filters
        # name is the parameter name on the filterset, f.name is the model field's name
        for name, f in six.iteritems(lookups_filters):
            opts.fields = {f.name: f.lookups or []}
            new_filters = new_class.filters_for_model(opts.model, opts)

            # filters_for_model generate param names from the model field name
            # replace model field name with the parameter name from the filerset
            new_class.base_filters.update(OrderedDict(
                (param.replace(f.name, name, 1), v)
                for param, v in six.iteritems(new_filters)
            ))

        # re-apply declared filters (sans `AllLookupsFilter`s)
        new_class.base_filters.update(declared_filters)

        # TODO: remove with deprecations
        for name, filter_ in six.iteritems(new_class.base_filters.copy()):
            if name not in new_class.declared_filters:
                new_class.base_filters[name] = fix_filter_field(filter_)

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


class FilterSet(six.with_metaclass(FilterSetMetaclass, rest_framework.FilterSet)):
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
                    self.filters[filter_name] = filters.BooleanFilter(name=filter_.name, lookup_expr='isnull')

            elif isinstance(filter_, filters.MethodFilter):
                filter_.resolve_action()

    @classmethod
    def filters_for_model(cls, model, opts):
        fields = opts.fields

        if not isinstance(fields, dict):
            return super(FilterSet, cls).filters_for_model(model, opts)

        # replace all '__all__' values by the resolved list of all lookups
        fields = fields.copy()
        for name, lookups in six.iteritems(fields):
            if lookups == filters.ALL_LOOKUPS:
                warnings.warn(
                    "ALL_LOOKUPS has been deprecated in favor of '__all__'. See: "
                    "https://github.com/philipn/django-rest-framework-filters/issues/62",
                    DeprecationWarning, stacklevel=2
                )
                lookups = '__all__'

            if lookups == '__all__':
                field = get_model_field(model, name)
                fields[name] = utils.lookups_for_field(field)

        return filterset.filters_for_model(
            model, fields, opts.exclude,
            cls.filter_for_field,
            cls.filter_for_reverse_field
        )

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
    @_base
    def fix_filter_field(cls, f):
        return f
