from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import six

from rest_framework.settings import api_settings
import rest_framework.filters
import django_filters
from django_filters.filters import *


def subsitute_iso8601(date_type):
    from rest_framework import ISO_8601 

    if date_type == 'datetime':
        strptime_iso8601 = '%Y-%m-%dT%H:%M:%S.%f'
        formats = api_settings.DATETIME_INPUT_FORMATS
    elif date_type == 'date':
        strptime_iso8601 = '%Y-%m-%d'
        formats = api_settings.DATE_INPUT_FORMATS
    elif date_type == 'time':
        strptime_iso8601 = '%H:%M:%S.%f'
        formats = api_settings.TIME_INPUT_FORMATS

    new_formats = []
    for f in formats:
        if f == ISO_8601:
            new_formats.append(strptime_iso8601)
        else:
            new_formats.append(f)
    return new_formats 


# In order to support ISO-8601 -- which is the default output for
# DRF -- we need to set up custom date/time input formats.
TIME_INPUT_FORMATS = subsitute_iso8601('time')
DATE_INPUT_FORMATS = subsitute_iso8601('date')
DATETIME_INPUT_FORMATS = subsitute_iso8601('datetime')


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
            cls = items[-1]
            mod = __import__('.'.join(items[:-1]), fromlist=[cls])
            self.filterset = getattr(mod, cls)

        self.extra['queryset'] = self.filterset._meta.model.objects.all()


class AllLookupsFilter(Filter):
    pass


###################################################
# Fixed-up versions of some of the default filters
###################################################

class DateFilter(django_filters.DateFilter):
    def __init__(self, *args, **kwargs):
        super(DateFilter, self).__init__(*args, **kwargs)
        self.extra.update({'input_formats': DATE_INPUT_FORMATS})


class DateTimeFilter(django_filters.DateTimeFilter):
    def __init__(self, *args, **kwargs):
        super(DateTimeFilter, self).__init__(*args, **kwargs)
        self.extra.update({'input_formats': DATETIME_INPUT_FORMATS})


class TimeFilter(django_filters.DateTimeFilter):
    def __init__(self, *args, **kwargs):
        super(TimeFilter, self).__init__(*args, **kwargs)
        self.extra.update({'input_formats': TIME_INPUT_FORMATS})
