from __future__ import absolute_import
from __future__ import unicode_literals

import warnings
from django.utils import six

from django_filters.rest_framework.filters import *

from . import fields


class ALL_LOOKUPS(object):
    pass


def _import_class(path):
    module_path, class_name = path.rsplit('.', 1)
    class_name = str(class_name)  # Ensure not unicode on py2.x
    module = __import__(module_path, fromlist=[class_name], level=0)
    return getattr(module, class_name)


class RelatedFilter(ModelChoiceFilter):
    def __init__(self, filterset, lookups=None, *args, **kwargs):
        self.filterset = filterset
        self.lookups = lookups
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

    @property
    def field(self):
        # if no queryset is provided, default to the filterset's default queryset
        self.extra.setdefault('queryset', self.filterset._meta.model._default_manager.all())
        return super(RelatedFilter, self).field


class AllLookupsFilter(Filter):
    lookups = '__all__'


###################################################
# Fixed-up versions of some of the default filters
###################################################

class InSetNumberFilter(Filter):
    field_class = fields.ArrayDecimalField

    def __init__(self, *args, **kwargs):
        super(InSetNumberFilter, self).__init__(*args, **kwargs)
        warnings.warn(
            'InSetNumberFilter is deprecated and no longer necessary. See: '
            'https://github.com/philipn/django-rest-framework-filters/issues/62',
            DeprecationWarning, stacklevel=2
        )


class InSetCharFilter(Filter):
    field_class = fields.ArrayCharField

    def __init__(self, *args, **kwargs):
        super(InSetCharFilter, self).__init__(*args, **kwargs)
        warnings.warn(
            'InSetCharFilter is deprecated and no longer necessary. See: '
            'https://github.com/philipn/django-rest-framework-filters/issues/62',
            DeprecationWarning, stacklevel=2
        )


class MethodFilter(Filter):
    """
    This filter will allow you to run a method that exists on the filterset class
    """

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', '')
        super(MethodFilter, self).__init__(*args, **kwargs)
        warnings.warn(
            'MethodFilter is deprecated and no longer necessary. See: '
            'https://github.com/philipn/django-rest-framework-filters/issues/109',
            DeprecationWarning, stacklevel=2
        )

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
