from django import forms


# https://code.djangoproject.com/ticket/19917
class Django14TimeField(forms.TimeField):
    input_formats = ['%H:%M:%S', '%H:%M:%S.%f', '%H:%M']


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
