import re
from collections import namedtuple
from urllib.parse import unquote

from django.db.models import QuerySet
from django.utils.translation import ugettext as _
from rest_framework.serializers import ValidationError

from rest_framework_filters.utils import lookahead

# originally based on: https://regex101.com/r/5rPycz/1
# current iteration: https://regex101.com/r/5rPycz/3
# special thanks to @JohnDoe2 on the #regex IRC channel!
# matches groups of "<negate>(<encoded querystring>)<set op>"
COMPLEX_OP_RE = re.compile(r'()\(([^)]+)\)([^(]*?(?=\())?')
COMPLEX_OP_NEG_RE = re.compile(r'(~?)\(([^)]+)\)([^(]*?(?=~\(|\())?')
COMPLEX_OPERATORS = {
    '&': QuerySet.__and__,
    '|': QuerySet.__or__,
}

ComplexOp = namedtuple('ComplexOp', ['querystring', 'negate', 'op'])


def decode_complex_ops(encoded_querystring, operators=None, negation=True):
    """
    Returns a list of (querystring, negate, op) tuples that represent complex operations.

    This function will raise a `ValidationError`s if:
    - the individual querystrings are not wrapped in parentheses
    - the set operators do not match the provided `operators`
    - there is trailing content after the ending querysting

    Ex::

        # unencoded query: (a=1) & (b=2) | ~(c=3)
        >>> s = '%28a%253D1%29%20%26%20%28b%253D2%29%20%7C%20%7E%28c%253D3%29'
        >>> decode_querystring_ops(s)
        [
            ('a=1', False, QuerySet.__and__),
            ('b=2', False, QuerySet.__or__),
            ('c=3', True, None),
        ]
    """
    complex_op_re = COMPLEX_OP_NEG_RE if negation else COMPLEX_OP_RE
    if operators is None:
        operators = COMPLEX_OPERATORS

    # decode into: (a%3D1) & (b%3D2) | ~(c%3D3)
    decoded_querystring = unquote(encoded_querystring)
    matches = [m for m in complex_op_re.finditer(decoded_querystring)]

    if not matches:
        msg = _("Unable to parse querystring. Decoded: '%(decoded)s'.")
        raise ValidationError(msg % {'decoded': decoded_querystring})

    results, errors = [], []
    for match, has_next in lookahead(matches):
        negate, querystring, op = match.groups()

        negate = negate == '~'
        querystring = unquote(querystring)
        op_func = operators.get(op.strip()) if op else None
        if op_func is None and has_next:
            msg = _("Invalid querystring operator. Matched: '%(op)s'.")
            errors.append(msg % {'op': op})

        results.append(ComplexOp(querystring, negate, op_func))

    trailing_chars = decoded_querystring[matches[-1].end():]
    if trailing_chars:
        msg = _("Ending querystring must not have trailing characters. Matched: '%(chars)s'.")
        errors.append(msg % {'chars': trailing_chars})

    if errors:
        raise ValidationError(errors)

    return results


def combine_complex_queryset(querysets, complex_ops, negation=True):
    # Negate querysets
    for queryset, op in zip(querysets, complex_ops):
        if negation and op.negate:
            queryset.query.where.negate()

    # Combine querysets
    combined = querysets[0]
    for queryset, op in zip(querysets[1:], complex_ops[:-1]):
        combined = op.op(combined, queryset)

    return combined
