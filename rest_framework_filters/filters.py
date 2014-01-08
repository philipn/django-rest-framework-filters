from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import six

from django_filters.filters import *


class RelatedFilter(ModelChoiceFilter):
    def __init__(self, filterset, *args, **kwargs):
        self.filterset = filterset
        super(RelatedFilter, self).__init__(*args, **kwargs)

    def setup_filterset(self):
        if isinstance(self.filterset, six.string_types):
            # This is a recursive relation, defined via a string, so we need
            # to create and import the class here.
            items = self.filterset.split('.')
            cls = items[-1]
            mod = __import__('.'.join(items[:-1]), fromlist=[cls])
            self.filterset = getattr(mod, cls)

        self.extra['queryset'] = self.filterset._meta.model.objects.all()


class AllLookupsFilter(Filter):
    pass
