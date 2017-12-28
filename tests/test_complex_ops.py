
from urllib.parse import quote

from django.db.models import QuerySet
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework_filters.complex_ops import decode_complex_ops


def encode(querysting):
    return quote(querysting) \
        .replace('-', '%2D')


class DecodeComplexOpsTests(TestCase):

    def test_docstring(self):
        encoded = '%28a%253D1%29%20%26%20%28b%253D2%29%20%7C%20%7E%28c%253D3%29'
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
            "Invalid querystring operator. Matched: ''."
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
        encoded = '%28a%253D1%29%20%26%20%7E%28b%253D2%29'
        readable = '(a%3D1) & ~(b%3D2)'
        result = [
            ('a=1', False, QuerySet.__and__),
            ('b=2', True, None),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_complex_ops(encoded), result)

    def test_duplicate_negation(self):
        encoded = '%28a%253D1%29%20%26%20%7E%7E%28b%253D2%29'
        readable = '(a%3D1) & ~~(b%3D2)'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_complex_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Invalid querystring operator. Matched: ' & ~'."
        ])
