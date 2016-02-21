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
    class_name = str(class_name)  # Ensure not unicode on py2.x
    module = __import__(module_path, fromlist=[class_name], level=0)
    return getattr(module, class_name)


class RelatedFilter(ModelChoiceFilter):
    def __init__(self, filterset, *args, **kwargs):
        self.filterset = filterset
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

    @property
    def field(self):
        # if no queryset is provided, default to the filterset's default queryset
        self.extra.setdefault('queryset', self.filterset._meta.model._default_manager.all())
        return super(RelatedFilter, self).field


class AllLookupsFilter(Filter):
    pass


###################################################
# Fixed-up versions of some of the default filters
###################################################
class BooleanFilter(BooleanFilter):
    field_class = fields.BooleanField


class InSetNumberFilter(Filter):
    field_class = fields.ArrayDecimalField


class InSetCharFilter(Filter):
    field_class = fields.ArrayCharField


class MethodFilter(Filter):
    """
    This filter will allow you to run a method that exists on the filterset class
    """

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', '')
        super(MethodFilter, self).__init__(*args, **kwargs)

    def resolve_action(self):
        """
        This method provides a hook for the parent FilterSet to resolve the filter's
        action after initialization. This is necessary, as the filter name may change
        as it's expanded across related filtersets.

        ie, `is_published` might become `post__is_published`.
        """
        # noop if a function was provided as the action
        if callable(self.action):
            return

        # otherwise, action is a string representing an action to be called on
        # the parent FilterSet.
        parent_action = self.action or 'filter_{0}'.format(self.name)

        parent = getattr(self, 'parent', None)
        self.action = getattr(parent, parent_action, None)

        assert callable(self.action), (
            'Expected parent FilterSet `%s.%s` to have a `.%s()` method.' %
            (parent.__class__.__module__, parent.__class__.__name__, parent_action)
        )

    def filter(self, qs, value):
        """
        This filter method will act as a proxy for the actual method we want to
        call.
        It will try to find the method on the parent filterset,
        if not it attempts to search for the method `field_{{attribute_name}}`.
        Otherwise it defaults to just returning the queryset.
        """
        return self.action(self.name, qs, value)
