import sys
from operator import attrgetter
from urllib.parse import quote

from django.db.models import QuerySet
from django.test import TestCase
from rest_framework.serializers import ValidationError

from rest_framework_filters.complex_ops import (
    ComplexOp, combine_complex_queryset, decode_complex_ops,
)
from tests.testapp import models


def encode(querysting):
    # Mimics the encoding logic of the client.
    result = quote(querysting)

    # Python 3.7 added '~' to the reserved character set.
    if sys.version_info < (3, 7):
        result = result.replace('%7E', '~')

    return result


class DecodeComplexOpsTests(TestCase):

    def test_docstring(self):
        encoded = '%28a%253D1%29%20%26%20%28b%253D2%29%20%7C%20~%28c%253D3%29'
        readable = '(a%3D1) & (b%3D2) | ~(c%3D3)'
        result = [
            ('a=1', False, QuerySet.__and__),
            ('b=2', False, QuerySet.__or__),
            ('c=3', True, None),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_complex_ops(encoded), result)

    def test_single_op(self):
        encoded = '%28a%253D1%29'
        readable = '(a%3D1)'
        result = [
            ('a=1', False, None),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_complex_ops(encoded), result)

    def test_op_spacing(self):
        encoded = '%28a%253D1%29%20%26%20%28b%253D2%29'
        readable = '(a%3D1) & (b%3D2)'
        result = [
            ('a=1', False, QuerySet.__and__),
            ('b=2', False, None),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_complex_ops(encoded), result)

    def test_missing_parens(self):
        encoded = 'a%253D1'
        readable = 'a%3D1'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_complex_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Unable to parse querystring. Decoded: 'a%3D1'.",
        ])

    def test_missing_closing_paren(self):
        encoded = '%28a%253D1'
        readable = '(a%3D1'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_complex_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Unable to parse querystring. Decoded: '(a%3D1'.",
        ])

    def test_missing_op(self):
        encoded = '%28a%253D1%29%28b%253D2%29%26%28c%253D3%29'
        readable = '(a%3D1)(b%3D2)&(c%3D3)'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_complex_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Invalid querystring operator. Matched: ''.",
        ])

    def test_invalid_ops(self):
        encoded = '%28a%253D1%29asdf%28b%253D2%29qwerty%28c%253D3%29%26'
        readable = '(a%3D1)asdf(b%3D2)qwerty(c%3D3)&'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_complex_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Invalid querystring operator. Matched: 'asdf'.",
            "Invalid querystring operator. Matched: 'qwerty'.",
            "Ending querystring must not have trailing characters. Matched: '&'.",
        ])

    def test_negation(self):
        encoded = '%28a%253D1%29%20%26%20~%28b%253D2%29'
        readable = '(a%3D1) & ~(b%3D2)'
        result = [
            ('a=1', False, QuerySet.__and__),
            ('b=2', True, None),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_complex_ops(encoded), result)

    def test_leading_negation(self):
        encoded = '~%28a%253D1%29%20%26%20%28b%253D2%29'
        readable = '~(a%3D1) & (b%3D2)'
        result = [
            ('a=1', True, QuerySet.__and__),
            ('b=2', False, None),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_complex_ops(encoded), result)

    def test_only_negation(self):
        encoded = '~%28a%253D1%29'
        readable = '~(a%3D1)'
        result = [
            ('a=1', True, None),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_complex_ops(encoded), result)

    def test_duplicate_negation(self):
        encoded = '%28a%253D1%29%20%26%20~~%28b%253D2%29'
        readable = '(a%3D1) & ~~(b%3D2)'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_complex_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Invalid querystring operator. Matched: ' & ~'.",
        ])

    def test_tilde_decoding(self):
        # Ensure decoding handles both RFC 2396 & 3986
        encoded_rfc3986 = '~%28a%253D1%29'
        encoded_rfc2396 = '%7E%28a%253D1%29'
        readable = '~(a%3D1)'
        result = [
            ('a=1', True, None),
        ]

        self.assertEqual(encode(readable), encoded_rfc3986)
        self.assertEqual(decode_complex_ops(encoded_rfc3986), result)
        self.assertEqual(decode_complex_ops(encoded_rfc2396), result)


class CombineComplexQuerysetTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        models.User.objects.create(username='u1', first_name='Bob', last_name='Jones')
        models.User.objects.create(username='u2', first_name='Joe', last_name='Jones')
        models.User.objects.create(username='u3', first_name='Bob', last_name='Smith')
        models.User.objects.create(username='u4', first_name='Joe', last_name='Smith')

    def test_single(self):
        querysets = [models.User.objects.filter(first_name='Bob')]
        complex_ops = [ComplexOp(None, False, None)]

        self.assertQuerysetEqual(
            combine_complex_queryset(querysets, complex_ops),
            ['u1', 'u3'], attrgetter('username'), False,
        )

    def test_AND(self):
        querysets = [
            models.User.objects.filter(first_name='Bob'),
            models.User.objects.filter(last_name='Jones'),
        ]
        complex_ops = [
            ComplexOp(None, False, QuerySet.__and__),
            ComplexOp(None, False, None),
        ]

        self.assertQuerysetEqual(
            combine_complex_queryset(querysets, complex_ops),
            ['u1'], attrgetter('username'), False,
        )

    def test_OR(self):
        querysets = [
            models.User.objects.filter(first_name='Bob'),
            models.User.objects.filter(last_name='Smith'),
        ]
        complex_ops = [
            ComplexOp(None, False, QuerySet.__or__),
            ComplexOp(None, False, None),
        ]

        self.assertQuerysetEqual(
            combine_complex_queryset(querysets, complex_ops),
            ['u1', 'u3', 'u4'], attrgetter('username'), False,
        )

    def test_negation(self):
        querysets = [
            models.User.objects.filter(first_name='Bob'),
            models.User.objects.filter(last_name='Smith'),
        ]
        complex_ops = [
            ComplexOp(None, False, QuerySet.__and__),
            ComplexOp(None, True, None),
        ]

        self.assertQuerysetEqual(
            combine_complex_queryset(querysets, complex_ops),
            ['u1'], attrgetter('username'), False,
        )
