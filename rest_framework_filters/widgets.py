
from __future__ import absolute_import
from __future__ import unicode_literals

from django import forms


# TODO: Remove when django-filter 0.12.0 is released
class BooleanWidget(forms.Widget):
    """Convert true/false values into the internal Python True/False.
    This can be used for AJAX queries that pass true/false from JavaScript's
    internal types through.
    """
    def value_from_datadict(self, data, files, name):
        """
        """
        value = super(BooleanWidget, self).value_from_datadict(
            data, files, name)

        if value is not None:
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False

        return value
