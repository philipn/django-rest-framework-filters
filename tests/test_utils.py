from django.test import TestCase

from rest_framework_filters import utils

from .testapp.models import Person, Note


class LookupsForFieldTests(TestCase):
    def test_standard_field(self):
        model_field = Person._meta.get_field('name')
        lookups = utils.lookups_for_field(model_field)

        self.assertIn('exact', lookups)
        self.assertNotIn('year', lookups)
        self.assertNotIn('date', lookups)

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


class LookupsForTransformTests(TestCase):
    def test_recursion_prevention(self):
        model_field = Person._meta.get_field('name')
        lookups = utils.lookups_for_field(model_field)

        self.assertIn('unaccent__exact', lookups)
        self.assertNotIn('unaccent__unaccent__exact', lookups)
