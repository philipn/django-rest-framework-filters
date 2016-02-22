
import warnings
from django.test import TestCase

from .filters import UserFilter


class FilterSetCacheDeprecationTests(TestCase):

    def test_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            cache = {}

            UserFilter({}, cache=cache)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

            self.assertIs(UserFilter._subset_cache, cache)
