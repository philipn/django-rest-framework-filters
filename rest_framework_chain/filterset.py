from __future__ import absolute_import
from __future__ import unicode_literals

from copy import copy

try:
    from django.db.models.constants import LOOKUP_SEP
except ImportError:  # pragma: nocover
    # Django < 1.5 fallback
    from django.db.models.sql.constants import LOOKUP_SEP  # noqa
from django.db import models
from django.utils.datastructures import SortedDict
from django.db.models.related import RelatedObject
from django.utils import six

import django_filters
from django_filters.filters import LOOKUP_TYPES
from django_filters.filterset import get_model_field
from rest_framework.settings import api_settings

from .filters import RelatedFilter, AllLookupsFilter


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

TIME_INPUT_FORMATS = subsitute_iso8601('time')
DATE_INPUT_FORMATS = subsitute_iso8601('date')
DATETIME_INPUT_FORMATS = subsitute_iso8601('datetime')


class FilterSet(django_filters.FilterSet):
    # In order to support ISO-8601 -- which is the default output for
    # DRF -- we need to set up custom date/time input formats.
    filter_overrides = {
        models.DateTimeField: {
            'filter_class': django_filters.DateTimeFilter,
            'extra': lambda f: {
                'input_formats': DATETIME_INPUT_FORMATS,
            }
        }, 
        models.DateField: {
            'filter_class': django_filters.DateFilter,
            'extra': lambda f: {
                'input_formats': DATE_INPUT_FORMATS,
            }
        }, 
        models.TimeField: {
            'filter_class': django_filters.TimeFilter,
            'extra': lambda f: {
                'input_formats': TIME_INPUT_FORMATS,
            }
        },
    }

    input_formats_lookup = {
        django_filters.TimeFilter: TIME_INPUT_FORMATS,
        django_filters.DateFilter: DATE_INPUT_FORMATS,
        django_filters.DateTimeFilter: DATETIME_INPUT_FORMATS,
    }

    def __init__(self, *args, **kwargs):
        super(FilterSet, self).__init__(*args, **kwargs)

        for name, filter_ in six.iteritems(self.filters):
            if isinstance(filter_, RelatedFilter):
                # Populate our FilterSet fields with the fields we've stored
                # in RelatedFilter.
                filter_.setup_filterset()
                self.populate_from_filterset(filter_.filterset, name)
            elif isinstance(filter_, AllLookupsFilter):
                # Populate our FilterSet fields with all the possible
                # filters for the AllLookupsFilter field.
                model = self._meta.model
                field = get_model_field(model, filter_.name)
                for lookup_type in LOOKUP_TYPES:
                    if isinstance(field, RelatedObject):
                        f = self.filter_for_reverse_field(field, filter_.name)
                    else:
                        f = self.filter_for_field(field, filter_.name)
                    f.lookup_type = lookup_type
                    self.filters["%s__%s" % (filter_.name, lookup_type)] = f
            elif self.is_time_filter(filter_):
                self.set_input_formats(filter_)

    def populate_from_filterset(self, filterset, name):
        """
        Populate `filters` with filters provided on `filterset`.
        """
        def _should_skip():
            for name, filter_ in six.iteritems(self.filters):
                if f == filter_:
                    return True
                # Avoid infinite recursion on recursive relations.  If the queryset and
                # class are the same, then we assume that we've already added this
                # filter previously along the lookup chain, e.g.
                # a__b__a <-- the last 'a' there.
                if isinstance(filter_, RelatedFilter) and isinstance(f, RelatedFilter):
                    if f.extra.get('queryset', None) == filter_.extra.get('queryset'):
                        return True
            return False
    
        for f in filterset.base_filters.values():
            if _should_skip():
                continue
    
            f = copy(f)
            f.name = '%s%s%s' % (name, LOOKUP_SEP, f.name)
            self.filters[f.name] = f

    def is_time_filter(self, f):
        if isinstance(f, django_filters.DateFilter):
            return True
        if isinstance(f, django_filters.DateTimeFilter):
            return True
        if isinstance(f, django_filters.TimeFilter):
            return True
        return False
    
    def set_input_formats(self, filter_):
        input_formats = filter_.extra.get('input_formats', [])
        if not input_formats:
            filter_.extra['input_formats'] = self.input_formats_lookup[filter_.__class__]

    #@classmethod
    #def filter_for_field(cls, f, name):
    #    if name == '
    #    import pdb;pdb.set_trace()
    #    cls.filter_overrides = FilterSet.filter_overrides
    #    return super(FilterSet, cls).filter_for_field(f, name)
