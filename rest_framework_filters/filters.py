from __future__ import absolute_import
from __future__ import unicode_literals

import django
from django.utils import six
from django_filters.filters import *

from . import fields


class RelatedFilter(ModelChoiceFilter):
    def __init__(self, filterset, *args, **kwargs):
        self.filterset = filterset
        self.parent_relation = kwargs.get('parent_relation', None)
        return super(RelatedFilter, self).__init__(*args, **kwargs)

    def setup_filterset(self):
        if isinstance(self.filterset, six.string_types):
            # This is a recursive relation, defined via a string, so we need
            # to create and import the class here.
            items = self.filterset.split('.')
            cls = str(items[-1])  # Ensure not unicode on py2.x
            mod = __import__('.'.join(items[:-1]), fromlist=[cls])
            self.filterset = getattr(mod, cls)

        self.extra['queryset'] = self.filterset._meta.model.objects.all()


class AllLookupsFilter(Filter):
    pass


###################################################
# Fixed-up versions of some of the default filters
###################################################

class TimeFilter(TimeFilter):
    if django.VERSION < (1, 6):
        field_class = fields.Django14TimeField


class InSetNumberFilter(NumberFilter):
    field_class = fields.ArrayDecimalField

    def filter(self, qs, value):
        if value in ([], (), {}, None, ''):
            return qs
        method = qs.exclude if self.exclude else qs.filter
        qs = method(**{self.name: value})
        if self.distinct:
            qs = qs.distinct()
        return qs
