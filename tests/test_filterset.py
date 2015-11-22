# -*- coding:utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import time
import datetime

from django.utils.dateparse import parse_time, parse_datetime

import django
from django.test import TestCase, override_settings
from django.contrib.auth.models import User

from .models import (
    Note, Post, Cover, Page, A, B, C, Person, Tag, BlogPost,
)

from .filters import (
    NoteFilterWithAll,
    # UserFilter,
    # UserFilterWithAll,
    NoteFilterWithRelated,
    NoteFilterWithRelatedAll,
    NoteFilterWithRelatedAllDifferentFilterName,
    PostFilterWithRelated,
    CoverFilterWithRelated,
    # PageFilterWithRelated,
    TagFilter,
    BlogPostFilter,
    # UserFilterWithDifferentName,
    NoteFilterWithRelatedDifferentName,

    # AFilter,
    # BFilter,
    CFilter,
    PersonFilter,

    AllLookupsPersonDateFilter,
    # ExplicitLookupsPersonDateFilter,
    InSetLookupPersonIDFilter,
    InSetLookupPersonNameFilter,
)


class TestFilterSets(TestCase):

    if django.VERSION >= (1, 8):
        @classmethod
        def setUpTestData(cls):
            cls.generateTestData()

    else:
        def setUp(self):
            self.generateTestData()

    @classmethod
    def generateTestData(cls):
        #######################
        # Create users
        #######################
        user1 = User(
            username="user1",
            email="user1@example.org"
        )
        user1.save()

        user2 = User(
            username="user2",
            email="user2@example.org"
        )
        user2.save()

        n = Note(
            title="Test 1",
            content="Test content 1",
            author=user1
        )
        n.save()

        #######################
        # Create notes
        #######################
        n = Note(
            title="Test 2",
            content="Test content 2",
            author=user1
        )
        n.save()

        n = Note(
            title="Hello Test 3",
            content="Test content 3",
            author=user1
        )
        n.save()

        n = Note(
            title="Hello Test 4",
            content="Test content 4",
            author=user2
        )
        n.save()

        #######################
        # Create posts
        #######################
        post = Post(
            note=Note.objects.get(title="Test 1"),
            content="Test content in post 1",
        )
        post.save()

        post = Post(
            note=Note.objects.get(title="Test 2"),
            content="Test content in post 2",
        )
        post.save()

        post = Post(
            note=Note.objects.get(title="Hello Test 4"),
            content="Test content in post 3",
        )
        post.save()

        #######################
        # Create covers
        #######################
        cover = Cover(
            post=Post.objects.get(note__title="Test 1"),
            comment="Cover 1"
        )
        cover.save()

        cover = Cover(
            post=Post.objects.get(note__title="Hello Test 4"),
            comment="Cover 2"
        )
        cover.save()

        #######################
        # Create pages
        #######################
        page = Page(
            title="First page",
            content="First first."
        )
        page.save()

        page = Page(
            title="Second page",
            content="Second second.",
            previous_page=Page.objects.get(title="First page")
        )
        page.save()

        ################################
        # ManyToMany
        ################################
        tag = Tag(name="park")
        tag.save()
        tag = Tag(name="lake")
        tag.save()
        tag = Tag(name="house")
        tag.save()

        blogpost = BlogPost(
            title="First post",
            content="First"
        )
        blogpost.save()
        blogpost.tags = [Tag.objects.get(name="park"), Tag.objects.get(name="house")]

        blogpost = BlogPost(
            title="Second post",
            content="Secon"
        )
        blogpost.save()
        blogpost.tags = [Tag.objects.get(name="house")]

        ################################
        # Recursive relations
        ################################
        a = A(title="A1")
        a.save()

        b = B(name="B1")
        b.save()

        c = C(title="C1")
        c.save()

        c.a = a
        c.save()
        a.b = b
        a.save()

        a = A(title="A2")
        a.save()

        c = C(title="C2")
        c.save()

        c = C(title="C3")
        c.save()

        p = Person(name="John")
        p.save()

        time.sleep(1)  # Created at least one second apart
        p = Person(name="Mark", best_friend=Person.objects.get(name="John"))
        p.save()


    def test_alllookupsfilter(self):
        # Test __iendswith
        GET = {
            'title__iendswith': '2',
        }
        f = NoteFilterWithAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Test 2")

        # Test __contains
        GET = {
            'title__contains': 'Test',
        }
        f = NoteFilterWithAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 4)

        # Test that the default exact filter works
        GET = {
            'title': 'Hello Test 3',
        }
        f = NoteFilterWithAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 3")

    def test_relatedfilter(self):
        # Test that the default exact filter works
        GET = {
            'author': User.objects.get(username='user2').pk,
        }
        f = NoteFilterWithRelated(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {
            'author__username': 'user2',
        }
        f = NoteFilterWithRelated(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

    def test_relatedfilter_combined_with_alllookups(self):
        # Test that the default exact filter works
        GET = {
            'author': User.objects.get(username='user2').pk,
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {
            'author__username': 'user2',
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        GET = {
            'author__username__endswith': '2',
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        GET = {
            'author__username__endswith': '1',
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 3)

        GET = {
            'author__username__contains': 'user',
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 4)

    def test_relatedfilter_combined_with_alllookups_and_different_filter_name(self):
        # Test that the default exact filter works
        GET = {
            'writer': User.objects.get(username='user2').pk,
        }
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {
            'writer__username': 'user2',
        }
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        GET = {
            'writer__username__endswith': '2',
        }
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        GET = {
            'writer__username__endswith': '1',
        }
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 3)

        GET = {
            'writer__username__contains': 'user',
        }
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 4)

    def test_relatedfilter_different_name(self):
        # Test the name filter on the related UserFilter set.
        GET = {
            'author__name': 'user2',
        }
        f = NoteFilterWithRelatedDifferentName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

    def test_double_relation_filter(self):
        GET = {
            'note__author__username__endswith': 'user2'
        }
        f = PostFilterWithRelated(GET, queryset=Post.objects.all())
        self.assertEqual(len(list(f)), 1)
        post = list(f)[0]
        self.assertEqual(post.content, "Test content in post 3")

    def test_triple_relation_filter(self):
        GET = {
            'post__note__author__username__endswith': 'user2'
        }
        f = CoverFilterWithRelated(GET, queryset=Cover.objects.all())
        self.assertEqual(len(list(f)), 1)
        cover = list(f)[0]
        self.assertEqual(cover.comment, "Cover 2")

    def test_indirect_recursive_relation(self):
        GET = {
            'a__b__name__endswith': '1'
        }
        f = CFilter(GET, queryset=C.objects.all())
        self.assertEqual(len(list(f)), 1)
        c = list(f)[0]
        self.assertEqual(c.title, "C1")

    def test_direct_recursive_relation(self):
        GET = {
            'best_friend__name__endswith': 'hn'
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f)), 1)
        p = list(f)[0]
        self.assertEqual(p.name, "Mark")

    def test_m2m_relation(self):
        GET = {
            'tags__name__endswith': 'ark',
        }
        f = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        self.assertEqual(len(list(f)), 1)
        p = list(f)[0]
        self.assertEqual(p.title, "First post")

        GET = {
            'tags__name__endswith': 'ouse',
        }
        f = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        self.assertEqual(len(list(f)), 2)
        titles = set([p.title for p in f])
        self.assertEqual(titles, set(["First post", "Second post"]))

    def test_implicit_date_filters(self):
        john = Person.objects.get(name="John")
        # Mark was created at least one second after John.
        mark = Person.objects.get(name="Mark")

        from rest_framework import serializers
        from rest_framework.renderers import JSONRenderer

        class PersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = Person

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
        self.assertEqual(len(list(f)), 2)
        p = list(f)[0]

        # DateTimeField
        GET = {
            'datetime_joined__lte': datetime_str,
        }
        f = AllLookupsPersonDateFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f)), 1)
        p = list(f)[0]
        self.assertEqual(p.name, "John")

        # TimeField
        GET = {
            'time_joined__lte': time_str,
        }
        f = AllLookupsPersonDateFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f)), 1)
        p = list(f)[0]
        self.assertEqual(p.name, "John")

    @override_settings(USE_TZ=True)
    def test_datetime_timezone_awareness(self):
        # Addresses issue #24 - ensure that datetime strings terminating
        # in 'Z' are correctly handled.
        from rest_framework import serializers
        from rest_framework.renderers import JSONRenderer

        class PersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = Person

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
        self.assertEqual(len(list(f)), 1)
        p = list(f)[0]
        self.assertEqual(p.name, "John")

    def test_inset_number_filter(self):
        p1 = Person.objects.get(name="John").pk
        p2 = Person.objects.get(name="Mark").pk

        ALL_GET = {
            'pk__in': '{:d},{:d}'.format(p1, p2),
        }
        f = InSetLookupPersonIDFilter(ALL_GET, queryset=Person.objects.all())
        f = [x.pk for x in f]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)


        INVALID_GET = {
            'pk__in': '{:d},c{:d}'.format(p1, p2)
        }
        f = InSetLookupPersonIDFilter(INVALID_GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f)), 0)

        EXTRA_GET = {
            'pk__in': '{:d},{:d},{:d}'.format(p1, p2, p1*p2)
        }
        f = InSetLookupPersonIDFilter(EXTRA_GET, queryset=Person.objects.all())
        f = [x.pk for x in f]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        DISORDERED_GET = {
            'pk__in': '{:d},{:d},{:d}'.format(p2, p2*p1, p1)
        }
        f = InSetLookupPersonIDFilter(DISORDERED_GET, queryset=Person.objects.all())
        f = [x.pk for x in f]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

    def test_get_filterset_subset(self):
        related_filter = NoteFilterWithRelated.base_filters['author']
        filterset_class = related_filter.get_filterset_subset(['email'])

        # ensure that the class name is useful when debugging
        self.assertEqual(filterset_class.__name__, 'UserFilterSubset')

        # ensure that the FilterSet subset only contains the requested fields
        self.assertIn('email', filterset_class.base_filters)
        self.assertEqual(len(filterset_class.base_filters), 1)

    def test_inset_char_filter(self):
        p1 = Person.objects.get(name="John").name
        p2 = Person.objects.get(name="Mark").name

        ALL_GET = {
            'name__in': '{},{}'.format(p1, p2),
        }
        f = InSetLookupPersonNameFilter(ALL_GET, queryset=Person.objects.all())
        f = [x.name for x in f]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        NONEXISTENT_GET = {
            'name__in': '{},Foo{}'.format(p1, p2)
        }
        f = InSetLookupPersonNameFilter(NONEXISTENT_GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f)), 1)

        EXTRA_GET = {
            'name__in': '{},{},{}'.format(p1, p2, p1+p2)
        }
        f = InSetLookupPersonNameFilter(EXTRA_GET, queryset=Person.objects.all())
        f = [x.name for x in f]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)

        DISORDERED_GET = {
            'name__in': '{},{},{}'.format(p2, p2+p1, p1)
        }
        f = InSetLookupPersonNameFilter(DISORDERED_GET, queryset=Person.objects.all())
        f = [x.name for x in f]
        self.assertEqual(len(f), 2)
        self.assertIn(p1, f)
        self.assertIn(p2, f)


class FilterSetExclutionTests(TestCase):

    if django.VERSION >= (1, 8):
        @classmethod
        def setUpTestData(cls):
            cls.generateTestData()

    else:
        def setUp(self):
            self.generateTestData()

    @classmethod
    def generateTestData(cls):
        t1 = Tag.objects.create(name='Tag 1')
        t2 = Tag.objects.create(name='Tag 2')
        t3 = Tag.objects.create(name='Something else entirely')

        p1 = BlogPost.objects.create(title='Post 1', content='content 1')
        p2 = BlogPost.objects.create(title='Post 2', content='content 2')

        p1.tags = [t1, t2]
        p2.tags = [t3]

    def test_exclude_property(self):
        """
        Ensure that the filter is set to exclude
        """
        GET = {
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        requested_filters = filterset.get_filters()

        self.assertTrue(requested_filters['name__contains!'].exclude)

    def test_filter_and_exclude(self):
        """
        Ensure that both the filter and exclusion filter are available
        """
        GET = {
            'name__contains': 'Tag',
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        requested_filters = filterset.get_filters()

        self.assertFalse(requested_filters['name__contains'].exclude)
        self.assertTrue(requested_filters['name__contains!'].exclude)

    def test_related_exclude(self):
        GET = {
            'tags__name__contains!': 'Tag',
        }

        filterset = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        requested_filters = filterset.get_filters()

        self.assertTrue(requested_filters['tags__name__contains!'].exclude)

    def test_exclusion_results(self):
        GET = {
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        results = [r.name for r in filterset]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Something else entirely')

    def test_filter_and_exclusion_results(self):
        GET = {
            'name__contains': 'Tag',
            'name__contains!': '2',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        results = [r.name for r in filterset]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Tag 1')

    def test_related_exclusion_results(self):
        GET = {
            'tags__name__contains!': 'Tag',
        }

        filterset = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        results = [r.title for r in filterset]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Post 2')
