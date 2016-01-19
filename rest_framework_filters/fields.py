from django import forms

# TODO: Remove when django-filter 0.12.0 is released
try:
    from django_filters import BooleanWidget
except ImportError:
    from .widgets import BooleanWidget


class BooleanField(forms.BooleanField):
    widget = BooleanWidget


class AbstractInField(object):
    def clean(self, value):
        if value is None:
            return None

        out = []
        for val in value.split(','):
            out.append(super(AbstractInField, self).clean(val))
        return out


class AbstractRangeField(object):
    def clean(self, value):
        if value is None:
            return None

        vals = value.split(',')
        if len(vals) != 2:
            raise ValueError('Range query expects 2 values.')

        out = []
        for val in vals:
            out.append(super(AbstractRangeField, self).clean(val))
        return out
