
from urllib.parse import quote

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework_filters.complex_ops import decode_querystring_ops


def encode(querysting):
    return quote(querysting) \
        .replace('-', '%2D')


class DecodeQuerystringOpsTests(TestCase):

    def test_docstring(self):
        encoded = '%28a%253D1%29%26%28b%253D2%29%7C%28c%253D3%29%2D%28d%253D4%29'
        readable = '(a%3D1)&(b%3D2)|(c%3D3)-(d%3D4)'
        result = [
            ('a=1', '&'),
            ('b=2', '|'),
            ('c=3', '-'),
            ('d=4', ''),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_querystring_ops(encoded), result)

    def test_single_op(self):
        encoded = '%28a%253D1%29'
        readable = '(a%3D1)'
        result = [
            ('a=1', ''),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_querystring_ops(encoded), result)

    def test_op_spacing(self):
        encoded = '%28a%253D1%29%20%26%20%28b%253D2%29'
        readable = '(a%3D1) & (b%3D2)'
        result = [
            ('a=1', '&'),
            ('b=2', ''),
        ]

        self.assertEqual(encode(readable), encoded)
        self.assertEqual(decode_querystring_ops(encoded), result)

    def test_missing_parens(self):
        encoded = 'a%253D1'
        readable = 'a%3D1'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_querystring_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Unable to parse querystring. Decoded: 'a%3D1'.",
        ])

    def test_missing_op(self):
        encoded = '%28a%253D1%29%28b%253D2%29%26%28c%253D3%29'
        readable = '(a%3D1)(b%3D2)&(c%3D3)'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_querystring_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Invalid querystring operator. Matched: ''."
        ])

    def test_invalid_ops(self):
        encoded = '%28a%253D1%29asdf%28b%253D2%29qwerty%28c%253D3%29%26'
        readable = '(a%3D1)asdf(b%3D2)qwerty(c%3D3)&'

        self.assertEqual(encode(readable), encoded)

        with self.assertRaises(ValidationError) as exc:
            decode_querystring_ops(encoded)

        self.assertEqual(exc.exception.detail, [
            "Invalid querystring operator. Matched: 'asdf'.",
            "Invalid querystring operator. Matched: 'qwerty'.",
            "Final querystring must not have an operator. Matched: '&'.",
        ])
