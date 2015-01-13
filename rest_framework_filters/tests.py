#-*- coding:utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import time
import datetime

from dateutil.parser import parse as date_parse

from django.db import models
from django.test import TestCase
from django.contrib.auth.models import User

from . import filters
from .filters import RelatedFilter, AllLookupsFilter
from .filterset import FilterSet
from .backends import DjangoFilterBackend


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey(User)


class Post(models.Model):
    note = models.ForeignKey(Note)
    content = models.TextField()


class Cover(models.Model):
    comment = models.CharField(max_length=100)
    post = models.ForeignKey(Post)


class Page(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    previous_page = models.ForeignKey('self', null=True)


class A(models.Model):
    title = models.CharField(max_length=100)
    b = models.ForeignKey('B', null=True)


class C(models.Model):
    title = models.CharField(max_length=100)
    a = models.ForeignKey(A, null=True)


class B(models.Model):
    name = models.CharField(max_length=100)
    c = models.ForeignKey(C, null=True)


class Person(models.Model):
    name = models.CharField(max_length=100)
    best_friend = models.ForeignKey('self', null=True)

    date_joined = models.DateField(auto_now=True)
    time_joined = models.TimeField(auto_now=True)
    datetime_joined = models.DateTimeField(auto_now=True)


class Tag(models.Model):
    name = models.CharField(max_length=100)


class BlogPost(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, null=True)


#################################################
# FilterSets
#################################################

class NoteFilterWithAll(FilterSet):
    title = AllLookupsFilter(name='title')

    class Meta:
        model = Note


class UserFilter(FilterSet):
    username = filters.CharFilter(name='username')
    email = filters.CharFilter(name='email')

    class Meta:
        model = User


class UserFilterWithAll(FilterSet):
    username = AllLookupsFilter(name='username')
    email = filters.CharFilter(name='email')

    class Meta:
        model = User


class NoteFilterWithRelated(FilterSet):
    title = filters.CharFilter(name='title')
    author = RelatedFilter(UserFilter, name='author')

    class Meta:
        model = Note


class NoteFilterWithRelatedAll(FilterSet):
    title = filters.CharFilter(name='title')
    author = RelatedFilter(UserFilterWithAll, name='author')

    class Meta:
        model = Note


class NoteFilterWithRelatedAllDifferentFilterName(FilterSet):
    title = filters.CharFilter(name='title')
    writer = RelatedFilter(UserFilterWithAll, name='author')

    class Meta:
        model = Note


class PostFilterWithRelated(FilterSet):
    note = RelatedFilter(NoteFilterWithRelatedAll, name='note')

    class Meta:
        model = Post


class CoverFilterWithRelated(FilterSet):
    comment = filters.CharFilter(name='comment')
    post = RelatedFilter(PostFilterWithRelated, name='post')

    class Meta:
        model = Cover


class PageFilterWithRelated(FilterSet):
    title = filters.CharFilter(name='title')
    previous_page = RelatedFilter(PostFilterWithRelated, name='previous_page')

    class Meta:
        model = Page


class TagFilter(FilterSet):
    name = AllLookupsFilter(name='name')

    class Meta:
        model = Tag


class BlogPostFilter(FilterSet):
    title = filters.CharFilter(name='title')
    tags = RelatedFilter(TagFilter, name='tags')

    class Meta:
        model = BlogPost


#############################################################
# Recursive filtersets
#############################################################
class AFilter(FilterSet):
    title = filters.CharFilter(name='title')
    b = RelatedFilter('rest_framework_filters.tests.BFilter', name='b')

    class Meta:
        model = A


class CFilter(FilterSet):
    title = filters.CharFilter(name='title')
    a = RelatedFilter(AFilter, name='a')

    class Meta:
        model = C


class BFilter(FilterSet):
    name = AllLookupsFilter(name='name')
    c = RelatedFilter(CFilter, name='c')

    class Meta:
        model = B


class PersonFilter(FilterSet):
    name = AllLookupsFilter(name='name')
    best_friend = RelatedFilter('rest_framework_filters.tests.PersonFilter', name='best_friend')

    class Meta:
        model = Person

#############################################################
# Extensions to django_filter fields for DRF.
#############################################################

class AllLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(name='date_joined')
    time_joined = AllLookupsFilter(name='time_joined')
    datetime_joined = AllLookupsFilter(name='datetime_joined')

    class Meta:
        model = Person


class ExplicitLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(name='date_joined')
    time_joined = AllLookupsFilter(name='time_joined')
    datetime_joined = AllLookupsFilter(name='datetime_joined')

    class Meta:
        model = Person


class TestFilterSets(TestCase):
    def setUp(self):
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
        datetime_str = JSONRenderer().render(date_parse(data['datetime_joined']) + datetime.timedelta(seconds=0.6)).decode('utf-8').strip('"')

        # Adjust for imprecise rendering of time
        dt = datetime.datetime.combine(datetime.date.today(), date_parse(data['time_joined']).time()) + datetime.timedelta(seconds=0.6)
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
