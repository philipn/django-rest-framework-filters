import copy
from collections import OrderedDict
from contextlib import contextmanager

from django.db.models.constants import LOOKUP_SEP
from django.http.request import QueryDict
from django_filters import filterset, rest_framework
from django_filters.utils import get_model_field

from . import filters, utils


class FilterSetMetaclass(filterset.FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(FilterSetMetaclass, cls).__new__(cls, name, bases, attrs)

        new_class.auto_filters = cls.get_auto_filters(new_class)
        new_class.related_filters = cls.get_related_filters(new_class)

        # If model is defined, process auto filters
        if new_class._meta.model is not None:
            cls.expand_auto_filters(new_class)

        return new_class

    @classmethod
    def expand_auto_filters(cls, new_class):
        # get reference to opts/declared filters
        orig_meta, orig_declared = new_class._meta, new_class.declared_filters

        # override opts/declared filters w/ copies
        new_class._meta = copy.deepcopy(new_class._meta)
        new_class.declared_filters = new_class.declared_filters.copy()

        for name, f in new_class.auto_filters.items():
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

    @classmethod
    def get_auto_filters(cls, new_class):
        return OrderedDict(
            (name, f) for name, f in new_class.declared_filters.items()
            if isinstance(f, filters.AutoFilter)
        )

    @classmethod
    def get_related_filters(cls, new_class):
        return OrderedDict(
            (name, f) for name, f in new_class.declared_filters.items()
            if isinstance(f, filters.RelatedFilter)
        )


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

        self.related_filtersets = self.get_related_filtersets()
        self.request_filters = self.get_request_filters()

    @classmethod
    def get_fields(cls):
        fields = super(FilterSet, cls).get_fields()

        for name, lookups in fields.items():
            if lookups == filters.ALL_LOOKUPS:
                field = get_model_field(cls._meta.model, name)
                fields[name] = utils.lookups_for_field(field)

        return fields

    def get_request_filters(self):
        """
        Build a set of filters based on the request data. This currently
        includes only filter exclusion/negation.
        """
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
        return requested_filters

    def get_related_filtersets(self):
        related_filtersets = OrderedDict()
        related_data = self.get_related_data(self.data)

        for related_name, subset_data in related_data.items():
            f = self.filters[related_name]
            related_filtersets[f.field_name] = f.filterset(
                data=subset_data,
                queryset=f.get_queryset(self.request),
                request=self.request,
                prefix=self.form_prefix,
            )

        return related_filtersets

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
    def get_related_data(cls, data):
        """
        Given the query data, return a map of {related filter: {related: data}}.
        The related data is used as the `data` argument for related FilterSet
        initialization.

        Note that the related data dictionaries will be a QueryDict, regardless
        of the type of the original data dict.

        ex::

            >>> NoteFilter.get_related_data({
            >>>     'author__email': 'foo',
            >>>     'author__name': 'bar',
            >>>     'name': 'baz',
            >>> })
            OrderedDict([
                ('author', <QueryDict: {'email': ['foo'], 'name': ['bar']}>)
            ])

        """
        related_filters = cls.related_filters.keys()
        related_data = OrderedDict()
        data = data.copy()  # get a copy of the original data

        # preference more specific filters. eg, `note__author` over `note`.
        for name in reversed(sorted(related_filters)):
            # we need to match against '__' to prevent eager matching against
            # like names. eg, note vs note2. Exact matches are handled above.
            related_prefix = "%s%s" % (name, LOOKUP_SEP)

            related = QueryDict('', mutable=True)
            for param in list(data):
                if param.startswith(related_prefix):
                    value = data.pop(param)
                    param = param[len(related_prefix):]

                    # handle QueryDict & dict values
                    if not isinstance(value, (list, tuple)):
                        related[param] = value
                    else:
                        related.setlist(param, value)

            if related:
                related_data[name] = related

        return related_data

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
    def override_filters(self):
        if self.is_bound:
            orig_filters = self.filters
            self.filters = self.request_filters
            yield
            self.filters = orig_filters

    def filter_queryset(self, queryset):
        with self.override_filters():
            queryset = super(FilterSet, self).filter_queryset(queryset)
            queryset = self.filter_related_filtersets(queryset)
            return queryset

    def get_form_class(self):
        with self.override_filters():
            return super(FilterSet, self).get_form_class()

    def filter_related_filtersets(self, queryset):
        """
        Filter the provided `qs` by the `related_filtersets`. It is recommended
        that you override this method to change the filtering behavior across
        relationships.
        """
        for field_name, related_filterset in self.related_filtersets.items():
            lookup_expr = LOOKUP_SEP.join([field_name, 'in'])
            queryset = queryset.filter(**{lookup_expr: related_filterset.qs})

        return queryset
