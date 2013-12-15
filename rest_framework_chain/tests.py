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


class Tag(models.Model):
    name = models.CharField(max_length=100)


class BlogPost(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, null=True)


#################################################
# FilterSets
#################################################

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


class PageFilterWithRelated(ChainedFilterSet):
    title = django_filters.CharFilter(name='title')
    previous_page = RelatedFilter(PostFilterWithRelated, name='previous_page')

    class Meta:
        model = Page


class TagFilter(ChainedFilterSet):
    name = AllLookupsFilter(name='name')

    class Meta:
        model = Tag


class BlogPostFilter(ChainedFilterSet):
    title = django_filters.CharFilter(name='title')
    tags = RelatedFilter(TagFilter, name='tags')

    class Meta:
        model = BlogPost


#############################################################
# Recursive filtersets
#############################################################
class AFilter(ChainedFilterSet):
    title = django_filters.CharFilter(name='title')
    b = RelatedFilter('rest_framework_chain.tests.BFilter', name='b')

    class Meta:
        model = A


class CFilter(ChainedFilterSet):
    title = django_filters.CharFilter(name='title')
    a = RelatedFilter(AFilter, name='a')

    class Meta:
        model = C


class BFilter(ChainedFilterSet):
    name = AllLookupsFilter(name='name')
    c = RelatedFilter(CFilter, name='c')

    class Meta:
        model = B


class PersonFilter(ChainedFilterSet):
    name = AllLookupsFilter(name='name')
    best_friend = RelatedFilter('rest_framework_chain.tests.PersonFilter', name='best_friend')

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
