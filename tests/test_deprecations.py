
import warnings
from django.test import TestCase

from rest_framework_filters import FilterSet

from .testapp.filters import UserFilter


class FilterSetCacheDeprecationTests(TestCase):

    def test_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            cache = {}

            UserFilter({}, cache=cache)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

            self.assertIs(UserFilter._subset_cache, cache)


class FixFilterFieldDeprecationTests(TestCase):

    def test_override_notifcation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                @classmethod
                def fix_filter_field(cls, f):
                    return super(F, cls).fix_filter_field(f)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_override_notifcation_without_invoking_base(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                @classmethod
                def fix_filter_field(cls, f):
                    return f

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_no_override_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                pass

            self.assertEqual(len(w), 0)
