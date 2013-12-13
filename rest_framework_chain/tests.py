#-*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.test import TestCase
from django.contrib.auth.models import User

import django_filters

from .filters import RelatedFilter, AllLookupsFilter
from .filterset import ChainedFilterSet


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


class NoteFilterWithAll(ChainedFilterSet):
    title = AllLookupsFilter(name='title')

    class Meta:
        model = Note


class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(name='username')
    email = django_filters.CharFilter(name='email')

    class Meta:
        model = User


class UserFilterWithAll(ChainedFilterSet):
    username = AllLookupsFilter(name='username')
    email = django_filters.CharFilter(name='email')

    class Meta:
        model = User


class NoteFilterWithRelated(ChainedFilterSet):
    title = django_filters.CharFilter(name='title')
    author = RelatedFilter(UserFilter, name='author')

    class Meta:
        model = Note


class NoteFilterWithRelatedAll(ChainedFilterSet):
    title = django_filters.CharFilter(name='title')
    author = RelatedFilter(UserFilterWithAll, name='author')

    class Meta:
        model = Note


class PostFilterWithRelated(ChainedFilterSet):
    note = RelatedFilter(NoteFilterWithRelatedAll, name='note')

    class Meta:
        model = Post


class CoverFilterWithRelated(ChainedFilterSet):
    comment = django_filters.CharFilter(name='comment')
    post = RelatedFilter(PostFilterWithRelated, name='post')

    class Meta:
        model = Cover


class TestAllLookupsFilter(TestCase):
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

        # Test the lookup filters on the related UserFilter set.
        GET = {
            'author__username__endswith': '2',
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 1)
        note = list(f)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the lookup filters on the related UserFilter set.
        GET = {
            'author__username__endswith': '1',
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 3)

        # Test the lookup filters on the related UserFilter set.
        GET = {
            'author__username__contains': 'user',
        }
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 4)

    def test_double_relation_filter(self):
        # Test that the default exact filter works
        GET = {
            'note__author__username__endswith': 'user2'
        }
        f = PostFilterWithRelated(GET, queryset=Post.objects.all())
        self.assertEqual(len(list(f)), 1)
        post = list(f)[0]
        self.assertEqual(post.content, "Test content in post 3")

    def test_triple_relation_filter(self):
        # Test that the default exact filter works
        GET = {
            'post__note__author__username__endswith': 'user2'
        }
        f = CoverFilterWithRelated(GET, queryset=Cover.objects.all())
        self.assertEqual(len(list(f)), 1)
        cover = list(f)[0]
        self.assertEqual(cover.comment, "Cover 2")
