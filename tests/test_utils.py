
import unittest
import django
from django.test import TestCase

from rest_framework_filters import utils

from .testapp.models import Person, Note


class LookupsForFieldTests(TestCase):
    def test_standard_field(self):
        model_field = Person._meta.get_field('name')
        lookups = utils.lookups_for_field(model_field)

        self.assertIn('exact', lookups)
        if django.VERSION >= (1, 9):
            self.assertNotIn('year', lookups)
            self.assertNotIn('date', lookups)
        else:
            self.assertIn('year', lookups)

    @unittest.skipIf(django.VERSION < (1, 9), "version does not support transformed lookup expressions")
    def test_transformed_field(self):
        model_field = Person._meta.get_field('datetime_joined')
        lookups = utils.lookups_for_field(model_field)

        self.assertIn('exact', lookups)
        self.assertIn('year__exact', lookups)
        self.assertIn('date__year__exact', lookups)

    def test_relation_field(self):
        # ForeignObject relations are special cased currently
        model_field = Note._meta.get_field('author')
        lookups = utils.lookups_for_field(model_field)

        self.assertIn('exact', lookups)
        self.assertIn('in', lookups)
        self.assertNotIn('regex', lookups)


@unittest.skipIf(django.VERSION < (1, 9), "version does not support transformed lookup expressions")
class LookupsForTransformTests(TestCase):
    def test_recursion_prevention(self):
        model_field = Person._meta.get_field('name')
        lookups = utils.lookups_for_field(model_field)

        self.assertIn('unaccent__exact', lookups)
        self.assertNotIn('unaccent__unaccent__exact', lookups)


class ClassLookupsTests(TestCase):
    def test_standard_field(self):
        model_field = Person._meta.get_field('name')
        class_lookups = utils.class_lookups(model_field)

        self.assertIn('exact', class_lookups)
        if django.VERSION >= (1, 9):
            self.assertNotIn('year', class_lookups)
            self.assertNotIn('date', class_lookups)
        else:
            self.assertIn('year', class_lookups)

    @unittest.skipIf(django.VERSION < (1, 9), "version does not support transformed lookup expressions")
    def test_transformed_field(self):
        model_field = Person._meta.get_field('datetime_joined')
        class_lookups = utils.class_lookups(model_field)

        self.assertIn('exact', class_lookups)
        self.assertIn('year', class_lookups)
        self.assertIn('date', class_lookups)
