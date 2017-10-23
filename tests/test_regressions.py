
"""
Regression tests for old `rest_framework_filters.FilterSet` functionality.

Code in this repository is occasionally made obsolete with improvements to the
underlying django-filter library. This module contains old tests that verify
that the FilterSet continue to behave as expected.
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

from django.test import TestCase, override_settings
from django.utils.dateparse import parse_time, parse_datetime

from rest_framework import serializers
from rest_framework.renderers import JSONRenderer

from .testapp.models import (
    User, Person, Note, Post, Cover,
)

from .testapp.filters import (
    UserFilter,
    AllLookupsPersonDateFilter,
    InSetLookupPersonIDFilter,
    InSetLookupPersonNameFilter,
    PostFilter,
    CoverFilterWithRelatedMethodFilter,
)


def add_timedelta(time, timedelta):
    dt = datetime.datetime.combine(datetime.datetime.today(), time)
    dt += timedelta
    return dt.time()


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['date_joined', 'time_joined', 'datetime_joined']


class IsoDatetimeTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        john = Person.objects.create(name="John")

        # Created at least one second apart
        mark = Person.objects.create(name="Mark", best_friend=john)
        mark.time_joined = add_timedelta(mark.time_joined, datetime.timedelta(seconds=1))
        mark.datetime_joined += datetime.timedelta(seconds=1)
        mark.save()

    def test_implicit_date_filters(self):
        john = Person.objects.get(name="John")
        # Mark was created at least one second after John.
        # mark = Person.objects.get(name="Mark")

        # Figure out what the date strings should look like based on the
        # serializer output.
        data = PersonSerializer(john).data

        date_str = JSONRenderer().render(data['date_joined']).decode('utf-8').strip('"')

        # Adjust for imprecise rendering of time
        datetime_str = JSONRenderer().render(parse_datetime(data['datetime_joined']) + datetime.timedelta(seconds=0.6)).decode('utf-8').strip('"')

        # Adjust for imprecise rendering of time
        dt = datetime.datetime.combine(datetime.date.today(), parse_time(data['time_joined'])) + datetime.timedelta(seconds=0.6)
        time_str = JSONRenderer().render(dt.time()).decode('utf-8').strip('"')

        # DateField
        GET = {
            'date_joined__lte': date_str,
        }
        f = AllLookupsPersonDateFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 2)
        p = list(f.qs)[0]

        # DateTimeField
        GET = {
            'datetime_joined__lte': datetime_str,
        }
        f = AllLookupsPersonDateFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "John")

        # TimeField
        GET = {
            'time_joined__lte': time_str,
        }
        f = AllLookupsPersonDateFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "John")

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_datetime_timezone_awareness(self):
        # Addresses issue #24 - ensure that datetime strings terminating
        # in 'Z' are correctly handled.

        # Figure out what the date strings should look like based on the
        # serializer output.
        john = Person.objects.get(name="John")
        data = PersonSerializer(john).data
        datetime_str = JSONRenderer().render(parse_datetime(data['datetime_joined']) + datetime.timedelta(seconds=0.6)).decode('utf-8').strip('"')

        # This is more for documentation - DRF appends a 'Z' to timezone aware UTC datetimes when rendering:
        # https://github.com/tomchristie/django-rest-framework/blob/3.2.0/rest_framework/fields.py#L1002-L1006
        self.assertTrue(datetime_str.endswith('Z'))

        GET = {
            'datetime_joined__lte': datetime_str,
        }
        f = AllLookupsPersonDateFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "John")


class BooleanFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username="user1", email="user1@example.org", is_active=True, last_login=datetime.date.today())
        User.objects.create(username="user2", email="user2@example.org", is_active=False)

    def test_boolean_filter(self):
        # Capitalized True
        GET = {'is_active': 'True'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user1')

        # Lowercase True
        GET = {'is_active': 'true'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user1')

        # Uppercase True
        GET = {'is_active': 'TRUE'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user1')

        # Capitalized False
        GET = {'is_active': 'False'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user2')

        # Lowercase False
        GET = {'is_active': 'false'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user2')

        # Uppercase False
        GET = {'is_active': 'FALSE'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user2')


class InLookupTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        john = Person.objects.create(name="John")
        Person.objects.create(name="Mark", best_friend=john)

        User.objects.create(username="user1", email="user1@example.org", is_active=True, last_login=datetime.date.today())
        User.objects.create(username="user2", email="user2@example.org", is_active=False)

    def test_inset_number_filter(self):
        p1 = Person.objects.get(name="John").pk
        p2 = Person.objects.get(name="Mark").pk

        ALL_GET = {
            'pk__in': '{:d},{:d}'.format(p1, p2),
        }
        f = InSetLookupPersonIDFilter(ALL_GET, queryset=Person.objects.all())
        f = [x.pk for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        INVALID_GET = {
            'pk__in': '{:d},c{:d}'.format(p1, p2)
        }
        f = InSetLookupPersonIDFilter(INVALID_GET, queryset=Person.objects.all())
        self.assertFalse(f.is_valid())
        self.assertEqual(f.qs.count(), 2)

        EXTRA_GET = {
            'pk__in': '{:d},{:d},{:d}'.format(p1, p2, p1*p2)
        }
        f = InSetLookupPersonIDFilter(EXTRA_GET, queryset=Person.objects.all())
        f = [x.pk for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        DISORDERED_GET = {
            'pk__in': '{:d},{:d},{:d}'.format(p2, p2*p1, p1)
        }
        f = InSetLookupPersonIDFilter(DISORDERED_GET, queryset=Person.objects.all())
        f = [x.pk for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

    def test_inset_char_filter(self):
        p1 = Person.objects.get(name="John").name
        p2 = Person.objects.get(name="Mark").name

        ALL_GET = {
            'name__in': '{},{}'.format(p1, p2),
        }
        f = InSetLookupPersonNameFilter(ALL_GET, queryset=Person.objects.all())
        f = [x.name for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        NONEXISTENT_GET = {
            'name__in': '{},Foo{}'.format(p1, p2)
        }
        f = InSetLookupPersonNameFilter(NONEXISTENT_GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)

        EXTRA_GET = {
            'name__in': '{},{},{}'.format(p1, p2, p1+p2)
        }
        f = InSetLookupPersonNameFilter(EXTRA_GET, queryset=Person.objects.all())
        f = [x.name for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        DISORDERED_GET = {
            'name__in': '{},{},{}'.format(p2, p2+p1, p1)
        }
        f = InSetLookupPersonNameFilter(DISORDERED_GET, queryset=Person.objects.all())
        f = [x.name for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)


class IsNullLookupTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username="user1", email="user1@example.org", is_active=True, last_login=datetime.date.today())
        User.objects.create(username="user2", email="user2@example.org", is_active=False)

    def test_isnull_override(self):
        import django_filters.filters

        self.assertIsInstance(
            UserFilter().filters['last_login__isnull'],
            django_filters.filters.BooleanFilter
        )

        GET = {'last_login__isnull': 'false'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user1')

        GET = {'last_login__isnull': 'true'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user2')


class FilterMethodTests(TestCase):
    """
    Old test case for MethodFilter. Ensure that the new Filter.method remains compatible.
    """

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username="user1", email="user1@example.org")

        note1 = Note.objects.create(title="Test 1", content="Test content 1", author=user)
        note2 = Note.objects.create(title="Test 2", content="Test content 2", author=user)

        post1 = Post.objects.create(note=note1, content="Test content in post 1")
        post2 = Post.objects.create(note=note2, content="Test content in post 2", date_published=datetime.date.today())

        Cover.objects.create(post=post1, comment="Cover 1")
        Cover.objects.create(post=post2, comment="Cover 2")

    def test_method_filter(self):
        GET = {
            'is_published': 'true'
        }
        filterset = PostFilter(GET, queryset=Post.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Test content in post 2")

    def test_related_method_filter(self):
        """
        Missing MethodFilter filter methods are silently ignored, returning
        the unfiltered queryset.
        """
        GET = {
            'post__is_published': 'true'
        }
        filterset = CoverFilterWithRelatedMethodFilter(GET, queryset=Cover.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].comment, "Cover 2")
