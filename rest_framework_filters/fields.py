
import warnings
from django import forms


class ArrayDecimalField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        super(ArrayDecimalField, self).__init__(*args, **kwargs)
        warnings.warn(
            'ArrayDecimalField is deprecated and no longer necessary. See: '
            'https://github.com/philipn/django-rest-framework-filters/issues/62',
            DeprecationWarning, stacklevel=3
        )

    def clean(self, value):
        if value is None:
            return None

        out = []
        for val in value.split(','):
            out.append(super(ArrayDecimalField, self).clean(val))
        return out


class ArrayCharField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(ArrayCharField, self).__init__(*args, **kwargs)
        warnings.warn(
            'ArrayCharField is deprecated and no longer necessary. See: '
            'https://github.com/philipn/django-rest-framework-filters/issues/62',
            DeprecationWarning, stacklevel=3
        )

    def clean(self, value):
        if value is None:
            return None

        out = []
        for val in value.split(','):
            out.append(super(ArrayCharField, self).clean(val))
        return out
