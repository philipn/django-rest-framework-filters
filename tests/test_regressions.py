"""
Regression tests for old `rest_framework_filters.FilterSet` functionality.

Code in this repository is occasionally made obsolete with improvements to the
underlying django-filter library. This module contains old tests that verify
that the FilterSet continue to behave as expected.
"""

import datetime

from django.test import TestCase, override_settings
from django.utils.dateparse import parse_datetime, parse_time
from rest_framework import serializers
from rest_framework.renderers import JSONRenderer

from rest_framework_filters import AutoFilter, FilterSet

from .testapp.filters import CoverFilter, PostFilter, UserFilter
from .testapp.models import Cover, Note, Person, Post, User

today = datetime.date.today()


def add_timedelta(time, timedelta):
    dt = datetime.datetime.combine(datetime.datetime.today(), time)
    dt += timedelta
    return dt.time()


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['date_joined', 'time_joined', 'datetime_joined']


class PersonFilter(FilterSet):
    date_joined = AutoFilter(field_name='date_joined', lookups='__all__')
    time_joined = AutoFilter(field_name='time_joined', lookups='__all__')
    datetime_joined = AutoFilter(field_name='datetime_joined', lookups='__all__')

    class Meta:
        model = Person
        fields = []


class InLookupPersonFilter(FilterSet):
    pk = AutoFilter('id', lookups='__all__')
    name = AutoFilter('name', lookups='__all__')

    class Meta:
        model = Person
        fields = []


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
        offset = parse_datetime(data['datetime_joined']) + datetime.timedelta(seconds=0.6)
        datetime_str = JSONRenderer().render(offset)
        datetime_str = datetime_str.decode('utf-8').strip('"')

        # Adjust for imprecise rendering of time
        offset = datetime.datetime.combine(today, parse_time(data['time_joined']))
        offset += datetime.timedelta(seconds=0.6)
        time_str = JSONRenderer().render(offset.time()).decode('utf-8').strip('"')

        # DateField
        GET = {
            'date_joined__lte': date_str,
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 2)
        p = list(f.qs)[0]

        # DateTimeField
        GET = {
            'datetime_joined__lte': datetime_str,
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "John")

        # TimeField
        GET = {
            'time_joined__lte': time_str,
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "John")

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_datetime_timezone_awareness(self):
        # Issue #24 - coorectly handle datetime strings terminating in 'Z'.

        # Figure out what the date strings should look like based on the serializer output
        john = Person.objects.get(name="John")
        data = PersonSerializer(john).data
        offset = parse_datetime(data['datetime_joined']) + datetime.timedelta(seconds=0.6)
        datetime_str = JSONRenderer().render(offset)
        datetime_str = datetime_str.decode('utf-8').strip('"')

        # DRF appends a 'Z' to timezone aware UTC datetimes when rendering:
        # https://github.com/tomchristie/django-rest-framework/blob/3.2.0/rest_framework/fields.py#L1002-L1006
        self.assertTrue(datetime_str.endswith('Z'))

        GET = {
            'datetime_joined__lte': datetime_str,
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "John")


class BooleanFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username="user1",
                            email="user1@example.org",
                            is_active=True,
                            last_login=today)
        User.objects.create(username="user2",
                            email="user2@example.org",
                            is_active=False)

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

        User.objects.create(username="user1",
                            email="user1@example.org",
                            is_active=True,
                            last_login=today)
        User.objects.create(username="user2",
                            email="user2@example.org",
                            is_active=False)

    def test_inset_number_filter(self):
        p1 = Person.objects.get(name="John").pk
        p2 = Person.objects.get(name="Mark").pk

        ALL_GET = {
            'pk__in': '{:d},{:d}'.format(p1, p2),
        }
        f = InLookupPersonFilter(ALL_GET, queryset=Person.objects.all())
        f = [x.pk for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        INVALID_GET = {
            'pk__in': '{:d},c{:d}'.format(p1, p2),
        }
        f = InLookupPersonFilter(INVALID_GET, queryset=Person.objects.all())
        self.assertFalse(f.is_valid())
        self.assertEqual(f.qs.count(), 2)

        EXTRA_GET = {
            'pk__in': '{:d},{:d},{:d}'.format(p1, p2, p1 * p2),
        }
        f = InLookupPersonFilter(EXTRA_GET, queryset=Person.objects.all())
        f = [x.pk for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        DISORDERED_GET = {
            'pk__in': '{:d},{:d},{:d}'.format(p2, p2 * p1, p1),
        }
        f = InLookupPersonFilter(DISORDERED_GET, queryset=Person.objects.all())
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
        f = InLookupPersonFilter(ALL_GET, queryset=Person.objects.all())
        f = [x.name for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        NONEXISTENT_GET = {
            'name__in': '{},Foo{}'.format(p1, p2),
        }
        f = InLookupPersonFilter(NONEXISTENT_GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)

        EXTRA_GET = {
            'name__in': '{},{},{}'.format(p1, p2, p1 + p2),
        }
        f = InLookupPersonFilter(EXTRA_GET, queryset=Person.objects.all())
        f = [x.name for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        DISORDERED_GET = {
            'name__in': '{},{},{}'.format(p2, p2 + p1, p1),
        }
        f = InLookupPersonFilter(DISORDERED_GET, queryset=Person.objects.all())
        f = [x.name for x in f.qs]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)


class IsNullLookupTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User.objects.create(username="user1",
                            email="user1@example.org",
                            is_active=True,
                            last_login=today)
        User.objects.create(username="user2",
                            email="user2@example.org",
                            is_active=False)

    def test_isnull_override(self):
        import django_filters.filters

        self.assertIsInstance(
            UserFilter.base_filters['last_login__isnull'],
            django_filters.filters.BooleanFilter,
        )

        GET = {'last_login__isnull': 'false'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        filter_ = filterset.filters['last_login__isnull']
        self.assertIsInstance(filter_, django_filters.filters.BooleanFilter)
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user1')

        GET = {'last_login__isnull': 'true'}
        filterset = UserFilter(GET, queryset=User.objects.all())
        filter_ = filterset.filters['last_login__isnull']
        self.assertIsInstance(filter_, django_filters.filters.BooleanFilter)
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, 'user2')


class FilterMethodTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create(username="user1", email="user1@example.org")

        note1 = Note.objects.create(title="Test 1", content="Test content 1", author=user)
        note2 = Note.objects.create(title="Test 2", content="Test content 2", author=user)

        post1 = Post.objects.create(note=note1, content="Test content in post 1")
        post2 = Post.objects.create(note=note2,
                                    content="Test content in post 2",
                                    publish_date=today)

        Cover.objects.create(post=post1, comment="Cover 1")
        Cover.objects.create(post=post2, comment="Cover 2")

    def test_method_filter(self):
        GET = {
            'is_published': 'true',
        }
        filterset = PostFilter(GET, queryset=Post.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Test content in post 2")

    def test_related_method_filter(self):
        # Missing MethodFilter methods are silently ignored, returning the unfiltered qs.
        GET = {
            'post__is_published': 'true',
        }
        filterset = CoverFilter(GET, queryset=Cover.objects.all())
        results = list(filterset.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].comment, "Cover 2")
