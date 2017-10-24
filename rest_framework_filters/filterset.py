from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
from contextlib import contextmanager
import copy

from django.db.models.constants import LOOKUP_SEP

from django_filters import filterset, rest_framework
from django_filters.utils import get_model_field

from . import filters
from . import utils


class FilterSetMetaclass(filterset.FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)

        # If no model is defined, skip auto filter processing
        if new_class._meta.model is None:
            return new_class

        opts = copy.deepcopy(new_class._meta)
        orig_meta = new_class._meta

        declared_filters = new_class.declared_filters.copy()
        orig_declared = new_class.declared_filters

        # Generate filters for auto filters
        auto_filters = OrderedDict([
            (param, f) for param, f in new_class.declared_filters.items()
            if isinstance(f, filters.AutoFilter)
        ])

        # Remove auto filters from declared_filters so that they *are* overwritten
        # RelatedFilter is an exception, and should *not* be overwritten
        for param, f in auto_filters.items():
            if not isinstance(f, filters.RelatedFilter):
                del declared_filters[param]

        for param, f in auto_filters.items():
            opts.fields = {f.field_name: f.lookups or []}

            # patch, generate auto filters
            new_class._meta, new_class.declared_filters = opts, declared_filters
            generated_filters = new_class.get_filters()

            # get_filters() generates param names from the model field name
            # Replace the field name with the parameter name from the filerset
            new_class.base_filters.update(OrderedDict(
                (gen_param.replace(f.field_name, param, 1), gen_f)
                for gen_param, gen_f in generated_filters.items()
            ))

        # Gather related filters
        new_class.related_filters = OrderedDict([
            (name, f) for name, f in new_class.base_filters.items()
            if isinstance(f, filters.RelatedFilter)
        ])

        new_class._meta, new_class.declared_filters = orig_meta, orig_declared

        return new_class


class FilterSet(rest_framework.FilterSet, metaclass=FilterSetMetaclass):

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None, **kwargs):
        # Filter the `base_filters` by the desired filter subset. This reduces the cost
        # of initialization by reducing the number of filters that are deepcopied.
        subset = self.get_filter_subset(data or {})
        if subset:
            self.base_filters = OrderedDict([
                (k, v) for k, v in self.base_filters.items() if k in subset
            ])

        super(FilterSet, self).__init__(data, queryset, request=request, prefix=prefix, **kwargs)

        self.expanded_filters = self.expand_filters()

    @classmethod
    def get_fields(cls):
        fields = super(FilterSet, cls).get_fields()

        for name, lookups in fields.items():
            if lookups == filters.ALL_LOOKUPS:
                field = get_model_field(cls._meta.model, name)
                fields[name] = utils.lookups_for_field(field)

        return fields

    def expand_filters(self):
        """
        Build a set of filters based on the requested data. The resulting set
        will walk `RelatedFilter`s to recursively build the set of filters.
        """
        # build param data for related filters: {rel: {param: value}}
        related_data = OrderedDict(
            [(name, OrderedDict()) for name in self.__class__.related_filters]
        )
        for param, value in self.data.items():
            filter_name, related_param = self.get_related_filter_param(param)

            # skip non lookup/related keys
            if filter_name is None:
                continue

            if filter_name in related_data:
                related_data[filter_name][related_param] = value

        # build the compiled set of all filters
        requested_filters = OrderedDict()
        for filter_name, f in self.filters.items():
            exclude_name = '%s!' % filter_name

            # Add plain lookup filters if match. ie, `username__icontains`
            if filter_name in self.data:
                requested_filters[filter_name] = f

            # include exclusion keys
            if exclude_name in self.data:
                # deepcopy the *base* filter to prevent copying of model & parent
                f_copy = copy.deepcopy(self.base_filters[filter_name])
                f_copy.parent = f.parent
                f_copy.model = f.model
                f_copy.exclude = not f.exclude

                requested_filters[exclude_name] = f_copy

            # include filters from related subsets
            if isinstance(f, filters.RelatedFilter) and filter_name in related_data:
                subset_data = related_data[filter_name]
                filterset = f.filterset(data=subset_data, request=self.request)

                # modify filter names to account for relationship
                for related_name, related_f in filterset.expand_filters().items():
                    related_name = LOOKUP_SEP.join([filter_name, related_name])
                    related_f.field_name = LOOKUP_SEP.join([f.field_name, related_f.field_name])
                    requested_filters[related_name] = related_f

        return requested_filters

    @classmethod
    def get_param_filter_name(cls, param):
        """
        Get the filter name for the request data parameter.

        ex::

            # regular attribute filters
            >>> FilterSet.get_param_filter_name('email')
            'email'

            # exclusion filters
            >>> FilterSet.get_param_filter_name('email!')
            'email'

            # related filters
            >>> FilterSet.get_param_filter_name('author__email')
            'author'

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
        for name in reversed(sorted(related_filters)):
            # we need to match against '__' to prevent eager matching against
            # like names. eg, note vs note2. Exact matches are handled above.
            if param.startswith("%s%s" % (name, LOOKUP_SEP)):
                return name

    @classmethod
    def get_related_filter_param(cls, param):
        """
        Get a tuple of (filter name, related param).

        ex::

            >>> FilterSet.get_related_filter_param('author__email__foobar')
            ('author', 'email__foobar')

            >>> FilterSet.get_related_filter_param('author')
            (None, None)

        """
        related_filters = cls.related_filters.keys()

        # preference more specific filters. eg, `note__author` over `note`.
        for name in reversed(sorted(related_filters)):
            # we need to match against '__' to prevent eager matching against
            # like names. eg, note vs note2. Exact matches are handled above.
            if param.startswith("%s%s" % (name, LOOKUP_SEP)):
                # strip param + LOOKUP_SET from param
                related_param = param[len(name) + len(LOOKUP_SEP):]
                return name, related_param

        # not a related param
        return None, None

    @classmethod
    def get_filter_subset(cls, params):
        """
        Returns a subset of filter names that should be initialized by the
        FilterSet, dependent on the requested `params`. This is useful when
        traversing FilterSet relationships, as it helps to minimize deepcopy
        overhead incurred when instantiating related FilterSets.
        """
        # Determine names of filters from query params and remove empty values.
        # param names that traverse relations are translated to just the local
        # filter names. eg, `author__username` => `author`. Empty values are
        # removed, as they indicate an unknown field eg, author__foobar__isnull
        filter_names = {cls.get_param_filter_name(param) for param in params}
        filter_names = {f for f in filter_names if f is not None}
        return filter_names

    @contextmanager
    def requested_filters(self):
        if self.is_bound:
            available_filters = self.filters
            requested_filters = self.expanded_filters

            self.filters = requested_filters
            yield
            self.filters = available_filters

    def filter_queryset(self, queryset):
        with self.requested_filters():
            return super(FilterSet, self).filter_queryset(queryset)

    def get_form_class(self):
        with self.requested_filters():
            return super(FilterSet, self).get_form_class()
