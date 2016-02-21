
from collections import OrderedDict

from django.db.models.constants import LOOKUP_SEP
from django.db.models.lookups import Transform
from django.utils import six


def lookups_for_field(model_field):
    """
    Generates a list of all possible lookup expressions for a model field.
    """
    lookups = []

    for expr, lookup in six.iteritems(class_lookups(model_field)):
        if issubclass(lookup, Transform):
            lookups += [
                LOOKUP_SEP.join([expr, transform]) for transform
                in lookups_for_field(lookup(model_field).output_field)
            ]
        else:
            lookups.append(expr)

    return lookups


def class_lookups(model_field):
    """
    Get a compiled set of class_lookups for a model field.
    """
    field_class = model_field.__class__
    class_lookups = OrderedDict()

    # traverse MRO in reverse, as this puts standard
    # lookups before subclass transforms/lookups
    for cls in field_class.mro()[::-1]:
        if hasattr(cls, 'class_lookups'):
            class_lookups.update(getattr(cls, 'class_lookups'))

    return class_lookups
