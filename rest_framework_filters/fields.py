from django import forms

# TODO: Remove when django-filter 0.12.0 is released
try:
    from django_filters import BooleanWidget
except ImportError:
    from .widgets import BooleanWidget


class BooleanField(forms.BooleanField):
    widget = BooleanWidget


class ArrayDecimalField(forms.DecimalField):
    def clean(self, value):
        if value is None:
            return None

        out = []
        for val in value.split(','):
            out.append(super(ArrayDecimalField, self).clean(val))
        return out


class ArrayCharField(forms.CharField):
    def clean(self, value):
        if value is None:
            return None

        out = []
        for val in value.split(','):
            out.append(super(ArrayCharField, self).clean(val))
        return out
