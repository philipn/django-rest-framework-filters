import re
from urllib.parse import unquote

from django.db.models import Q
from django.utils.translation import ugettext as _

from rest_framework.serializers import ValidationError


# see: https://regex101.com/r/9MiZ7n/7
# essentially we want to match groups of "(<encoded querystring>)<set op>"
# special thanks to @JohnDoe2 on the #regex IRC channel!
QUERYSTRING_OP_RE = re.compile(r'\(([^)]+)\)([^()]*)?')

OPERATORS = {
    '&': lambda a, b: a & b,
    '|': lambda a, b: a | b,
    '-': lambda a, b: a & ~Q(b),
}


def decode_querystring_ops(encoded_querystring):
    """
    Returns a list of (querystring, op) pairs given the `encoded_querystring`.

    This function will raise a `ValidationError`s if:
    - the leading decoded character is not an opening '('
    - the set operators do not match (&, |, or -)
    - there is a trailing operator after the last querysting

    Ex::

        # unencoded query: (a=1) & (b=2) | (c=3) - (d=4)
        >>> s = '%28a%253D1%29%26%28b%253D2%29%7C%28c%253D3%29-%28d%253D4%29'
        >>> decode_querystring_ops(s)
        [
            ('a=1', '&'),
            ('b=2', '|'),
            ('c=3', '-'),
            ('d=4', ''),
        ]
    """
    # decode into: (a%3D1)&(b%3D2)|(c%3D3)-(d%3D4)
    decoded_querystring = unquote(encoded_querystring)
    result = QUERYSTRING_OP_RE.findall(decoded_querystring)

    if not result:
        raise ValidationError(
            _("Unable to parse querystring. Decoded: '%(decoded)s'.") % {
                'decoded': decoded_querystring
            }
        )

    errors = []
    for __, op in result[:-1]:
        if op.strip() not in OPERATORS:
            msg = _("Invalid querystring operator. Matched: '%(op)s'.")
            errors.append(msg % {'op': op})

    if result[-1][1].strip() != '':
        msg = _("Final querystring must not have an operator. Matched: '%(op)s'.")
        errors.append(msg % {'op': result[-1][1]})

    if errors:
        raise ValidationError(errors)

    return [(unquote(querysting), op.strip()) for querysting, op in result]
