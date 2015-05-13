from django import forms

class ArrayDecimalField(forms.DecimalField):
    def clean(self, value):
        out = []
        for val in value.split(','):
            out.append(super(ArrayDecimalField, self).clean(val))
        return out
