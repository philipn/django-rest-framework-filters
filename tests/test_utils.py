from django.test import TestCase

from rest_framework_filters import utils

from .testapp.models import Note, Person


class ImportClassTests(TestCase):
    def test_simple(self):
        cls = utils.import_class('tests.testapp.models.Note')

        self.assertEqual(cls.__module__, 'tests.testapp.models')
        self.assertEqual(cls.__name__, 'Note')
        self.assertIs(cls, Note)


class RelativeClassPathTests(TestCase):
    def test_is_full_path(self):
        path = utils.relative_class_path(None, 'a.b.c')

        self.assertEqual(path, 'a.b.c')

    def test_prepend_relative_class(self):
        path = utils.relative_class_path(Note, 'Test')

        self.assertEqual(path, 'tests.testapp.models.Test')

    def test_prepend_relative_instance(self):
        path = utils.relative_class_path(Note(), 'Test')

        self.assertEqual(path, 'tests.testapp.models.Test')


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


class LookaheadTests(TestCase):
    def test_empty(self):
        result = list(utils.lookahead([]))
        self.assertListEqual(result, [])

    def test_single(self):
        result = list(utils.lookahead([1]))
        self.assertListEqual(result, [(1, False)])

    def test_multiple(self):
        result = list(utils.lookahead([1, 2, 3]))
        self.assertListEqual(result, [
            (1, True),
            (2, True),
            (3, False),
        ])
