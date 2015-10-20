from __future__ import absolute_import
from __future__ import unicode_literals

from collections import OrderedDict
from django.utils import six

from django_filters.filters import *
from django_filters.filters import LOOKUP_TYPES

from . import fields

ALL_LOOKUPS = LOOKUP_TYPES


def _import_class(path):
    module_path, class_name = path.rsplit('.', 1)
    class_name = str(class_name) # Ensure not unicode on py2.x
    module = __import__(module_path, fromlist=[class_name], level=0)
    return getattr(module, class_name)


class RelatedFilter(ModelChoiceFilter):
    def __init__(self, filterset, *args, **kwargs):
        self.filterset = filterset
        # self.parent_relation = kwargs.get('parent_relation', None)
        return super(RelatedFilter, self).__init__(*args, **kwargs)

    def filterset():
        def fget(self):
            if isinstance(self._filterset, six.string_types):
                self._filterset = _import_class(self._filterset)
            return self._filterset

        def fset(self, value):
            self._filterset = value

        return locals()
    filterset = property(**filterset())

    def get_filterset_subset(self, filter_names):
        """
        Returns a FilterSet subclass that contains the subset of filters
        specified in `filter_names`. This is useful for creating FilterSets
        used across relationships, as it minimizes the deepcopy overhead
        incurred when instantiating the FilterSet.
        """
        BaseFilterSet = self.filterset

        class FilterSetSubset(BaseFilterSet):
            pass

        FilterSetSubset.__name__ = str('%sSubset' % (BaseFilterSet.__name__))
        FilterSetSubset.base_filters = OrderedDict([
            (name, f)
            for name, f in six.iteritems(BaseFilterSet.base_filters)
            if name in filter_names
        ])

        return FilterSetSubset

    def setup_filterset(self):
        self.extra['queryset'] = self.filterset._meta.model.objects.all()


class AllLookupsFilter(Filter):
    pass


###################################################
# Fixed-up versions of some of the default filters
###################################################

class InSetFilterBase(object):
    def filter(self, qs, value):
        if value in ([], (), {}, None, ''):
            return qs
        method = qs.exclude if self.exclude else qs.filter
        qs = method(**{self.name: value})
        if self.distinct:
            qs = qs.distinct()
        return qs


class InSetNumberFilter(InSetFilterBase, NumberFilter):
    field_class = fields.ArrayDecimalField


class InSetCharFilter(InSetFilterBase, NumberFilter):
    field_class = fields.ArrayCharField
