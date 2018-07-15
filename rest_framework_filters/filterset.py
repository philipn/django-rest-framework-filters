import copy
from collections import OrderedDict
from contextlib import contextmanager

from django.db.models.constants import LOOKUP_SEP
from django_filters import filterset, rest_framework
from django_filters.utils import get_model_field

from . import filters, utils


class FilterSetMetaclass(filterset.FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)

        new_class.auto_filters = [
            name for name, f in new_class.declared_filters.items()
            if isinstance(f, filters.AutoFilter)]
        new_class.related_filters = [
            name for name, f in new_class.declared_filters.items()
            if isinstance(f, filters.RelatedFilter)]

        # see: :meth:`rest_framework_filters.filters.RelatedFilter.bind`
        for name in new_class.related_filters:
            new_class.declared_filters[name].bind(new_class)

        # If model is defined, process auto filters
        if new_class._meta.model is not None:
            cls.expand_auto_filters(new_class)

        return new_class

    @classmethod
    def expand_auto_filters(cls, new_class):
        """
        Resolve `AutoFilter`s into their per-lookup filters. `AutoFilter`s are
        a declarative alternative to the `Meta.fields` dictionary syntax, and
        use the same machinery internally.
        """
        # get reference to opts/declared filters
        orig_meta, orig_declared = new_class._meta, new_class.declared_filters

        # override opts/declared filters w/ copies
        new_class._meta = copy.deepcopy(new_class._meta)
        new_class.declared_filters = new_class.declared_filters.copy()

        for name in new_class.auto_filters:
            f = new_class.declared_filters[name]

            # Remove auto filters from declared_filters so that they *are* overwritten
            # RelatedFilter is an exception, and should *not* be overwritten
            if not isinstance(f, filters.RelatedFilter):
                del new_class.declared_filters[name]

            # Use meta.fields to generate auto filters
            new_class._meta.fields = {f.field_name: f.lookups or []}
            for gen_name, gen_f in new_class.get_filters().items():
                # get_filters() generates param names from the model field name
                # Replace the field name with the parameter name from the filerset
                gen_name = gen_name.replace(f.field_name, name, 1)
                new_class.base_filters[gen_name] = gen_f

        # restore reference to opts/declared filters
        new_class._meta, new_class.declared_filters = orig_meta, orig_declared


class SubsetDisabledMixin:
    """
    Used to disable filter subsetting (see: :meth:`FilterSet.disable_subset`).
    """
    @classmethod
    def get_filter_subset(cls, params, rel=None):
        return cls.base_filters

    @contextmanager
    def override_filters(self):
        yield


class FilterSet(rest_framework.FilterSet, metaclass=FilterSetMetaclass):

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None, **kwargs):
        # Filter the `base_filters` by the desired filter subset. This reduces the cost
        # of initialization by reducing the number of filters that are deepcopied.
        self.base_filters = self.get_filter_subset(data or {})

        super(FilterSet, self).__init__(data, queryset, request=request, prefix=prefix, **kwargs)

        self.request_filters = self.get_request_filters()

    @classmethod
    def get_fields(cls):
        fields = super(FilterSet, cls).get_fields()

        for name, lookups in fields.items():
            if lookups == filters.ALL_LOOKUPS:
                field = get_model_field(cls._meta.model, name)
                fields[name] = utils.lookups_for_field(field)

        return fields

    @classmethod
    def get_filter_subset(cls, params):
        """
        Returns the subset of filters that should be initialized by the
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
        return OrderedDict(
            (k, v) for k, v in cls.base_filters.items() if k in filter_names
        )

    @classmethod
    def disable_subset(cls):
        """
        Disable filter subsetting, allowing the form to render the filterset.
        Note that this decreases performance and should only be used when
        rendering a form, such as with DRF's browsable API.
        """
        if not issubclass(cls, SubsetDisabledMixin):
            return type('SubsetDisabled%s' % cls.__name__,
                        (SubsetDisabledMixin, cls), {})
        return cls

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

    def get_request_filters(self):
        """
        Build a set of filters based on the request data. The resulting set
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
                for related_name, related_f in filterset.get_request_filters().items():
                    related_name = LOOKUP_SEP.join([filter_name, related_name])
                    related_f.field_name = LOOKUP_SEP.join([f.field_name, related_f.field_name])
                    requested_filters[related_name] = related_f

        return requested_filters

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

    @contextmanager
    def override_filters(self):
        if not self.is_bound:
            yield
        else:
            orig_filters = self.filters
            self.filters = self.request_filters
            yield
            self.filters = orig_filters

    def filter_queryset(self, queryset):
        with self.override_filters():
            return super(FilterSet, self).filter_queryset(queryset)

    def get_form_class(self):
        with self.override_filters():
            return super(FilterSet, self).get_form_class()
