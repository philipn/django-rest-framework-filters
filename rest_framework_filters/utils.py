
from collections import OrderedDict

import django
from django.db.models.constants import LOOKUP_SEP
from django.db.models.expressions import Expression
from django.db.models.fields.related import ForeignObject
from django.db.models.lookups import Transform
from django.utils import six


def import_class(path):
    module_path, class_name = path.rsplit('.', 1)
    class_name = str(class_name)  # Ensure not unicode on py2.x
    module = __import__(module_path, fromlist=[class_name], level=0)
    return getattr(module, class_name)


def lookups_for_field(model_field):
    """
    Generates a list of all possible lookup expressions for a model field.
    """
    # This is a hack to work around:
    # https://github.com/django/django/pull/6906
    if isinstance(model_field, ForeignObject):
        return ['exact', 'gt', 'gte', 'lt', 'lte', 'in', 'isnull']

    lookups = []

    for expr, lookup in six.iteritems(class_lookups(model_field)):
        if issubclass(lookup, Transform) and django.VERSION >= (1, 9):
            transform = lookup(Expression(model_field))
            lookups += [
                LOOKUP_SEP.join([expr, sub_expr]) for sub_expr
                in lookups_for_transform(transform)
            ]

        else:
            lookups.append(expr)

    return lookups


def lookups_for_transform(transform):
    """
    Generates a list of subsequent lookup expressions for a transform.

    Note:
    Infinite transform recursion is only prevented when the subsequent and
    passed in transforms are the same class. For example, the ``Unaccent``
    transform from ``django.contrib.postgres``.
    There is no cycle detection across multiple transforms. For example,
    ``a__b__a__b`` would continue to recurse. However, this is not currently
    a problem (no builtin transforms exhibit this behavior).

    """
    lookups = []

    for expr, lookup in six.iteritems(class_lookups(transform.output_field)):
        if issubclass(lookup, Transform):

            # type match indicates recursion.
            if type(transform) == lookup:
                continue

            sub_transform = lookup(transform)
            lookups += [
                LOOKUP_SEP.join([expr, sub_expr]) for sub_expr
                in lookups_for_transform(sub_transform)
            ]

        else:
            lookups.append(expr)

    return lookups


def class_lookups(model_field):
    """
    Get a compiled set of class_lookups for a model field.
    """
    field_class = type(model_field)
    class_lookups = OrderedDict()

    # traverse MRO in reverse, as this puts standard
    # lookups before subclass transforms/lookups
    for cls in reversed(field_class.mro()):
        if hasattr(cls, 'class_lookups'):
            class_lookups.update(getattr(cls, 'class_lookups'))

    return class_lookups
