
from __future__ import absolute_import
from __future__ import unicode_literals

from django.test import TestCase

from rest_framework_filters.compat import set_many
from rest_framework_filters import FilterSet, filters
from django_filters import FilterSet as DFFilterSet

from .testapp.models import (
    User, Note, Post, Cover, Page, A, B, C, Person, Tag, BlogPost,
)

from .testapp.filters import (
    UserFilter,
    PersonFilter,
    PostFilter,
    BlogPostFilter,
    CoverFilterWithRelated,
    PageFilterWithAliasedNestedRelated,
    NoteFilterWithAll,
    NoteFilterWithRelated,
    NoteFilterWithRelatedDifferentName,
    NoteFilterWithRelatedAll,
    NoteFilterWithRelatedAllDifferentFilterName,
    CFilter,
)


class AllLookupsFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        #######################
        # Create users
        #######################
        user1 = User.objects.create(username="user1", email="user1@example.org")
        user2 = User.objects.create(username="user2", email="user2@example.org")

        #######################
        # Create notes
        #######################
        Note.objects.create(title="Test 1", content="Test content 1", author=user1)
        Note.objects.create(title="Test 2", content="Test content 2", author=user1)
        Note.objects.create(title="Hello Test 3", content="Test content 3", author=user1)
        Note.objects.create(title="Hello Test 4", content="Test content 4", author=user2)

    def test_alllookupsfilter(self):
        # Test __iendswith
        GET = {'title__iendswith': '2'}
        f = NoteFilterWithAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Test 2")

        # Test __contains
        GET = {'title__contains': 'Test'}
        f = NoteFilterWithAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

        # Test that the default exact filter works
        GET = {'title': 'Hello Test 3'}
        f = NoteFilterWithAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 3")

    def test_alllookups_filter_with_mixin(self):
        # Mixin FilterSets should not error when no model is provided. See:
        # https://github.com/philipn/django-rest-framework-filters/issues/82
        class Mixin(FilterSet):
            title = filters.AllLookupsFilter()

        class Actual(Mixin):
            class Meta:
                model = Note
                fields = []

        GET = {'title__contains': 'Test'}
        f = Actual(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)


class RelatedFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        #######################
        # Create users
        #######################
        user1 = User.objects.create(username="user1", email="user1@example.org")
        user2 = User.objects.create(username="user2", email="user2@example.org")

        #######################
        # Create notes
        #######################
        note1 = Note.objects.create(title="Test 1", content="Test content 1", author=user1)
        note2 = Note.objects.create(title="Test 2", content="Test content 2", author=user1)
        Note.objects.create(title="Hello Test 3", content="Test content 3", author=user1)
        note4 = Note.objects.create(title="Hello Test 4", content="Test content 4", author=user2)

        #######################
        # Create posts
        #######################
        post1 = Post.objects.create(note=note1, content="Test content in post 1")
        Post.objects.create(note=note2, content="Test content in post 2")
        post3 = Post.objects.create(note=note4, content="Test content in post 3")

        #######################
        # Create covers
        #######################
        Cover.objects.create(post=post1, comment="Cover 1")
        Cover.objects.create(post=post3, comment="Cover 2")

        #######################
        # Create pages
        #######################
        Page.objects.create(title="First page", content="First first.")
        Page.objects.create(title="Second page", content="Second second.", previous_page_id=1)
        Page.objects.create(title="Third page", content="Third third.", previous_page_id=2)
        Page.objects.create(title="Fourth page", content="Fourth fourth.", previous_page_id=3)

        ################################
        # ManyToMany
        ################################
        t1 = Tag.objects.create(name="park")
        Tag.objects.create(name="lake")
        t3 = Tag.objects.create(name="house")

        blogpost = BlogPost.objects.create(title="First post", content="First")
        set_many(blogpost, 'tags', [t1, t3])

        blogpost = BlogPost.objects.create(title="Second post", content="Secon")
        set_many(blogpost, 'tags', [t3])

        ################################
        # Recursive relations
        ################################
        a = A.objects.create(title="A1")
        b = B.objects.create(name="B1")
        c = C.objects.create(title="C1")

        c.a = a
        c.save()

        a.b = b
        a.save()

        A.objects.create(title="A2")
        C.objects.create(title="C2")
        C.objects.create(title="C3")

        john = Person.objects.create(name="John")
        Person.objects.create(name="Mark", best_friend=john)

    def test_relatedfilter(self):
        # Test that the default exact filter works
        GET = {'author': User.objects.get(username='user2').pk}
        f = NoteFilterWithRelated(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {'author__username': 'user2'}
        f = NoteFilterWithRelated(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

    def test_relatedfilter_for_related_alllookups(self):
        # ensure that filters work for AllLookupsFilter across a RelatedFilter.

        # Test that the default exact filter works
        GET = {'author': User.objects.get(username='user2').pk}
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        note = list(f.qs)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {'author__username': 'user2'}
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'author__username__endswith': '2'}
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'author__username__endswith': '1'}
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 3)

        GET = {'author__username__contains': 'user'}
        f = NoteFilterWithRelatedAll(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

    def test_relatedfilter_for_related_alllookups_and_different_filter_name(self):
        # Test that the default exact filter works
        GET = {
            'writer': User.objects.get(username='user2').pk,
        }
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        note = list(f.qs)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {'writer__username': 'user2'}
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'writer__username__endswith': '2'}
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'writer__username__endswith': '1'}
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 3)

        GET = {'writer__username__contains': 'user'}
        f = NoteFilterWithRelatedAllDifferentFilterName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

    def test_relatedfilter_for_aliased_nested_relationships(self):
        qs = Page.objects.order_by('pk')

        f1 = PageFilterWithAliasedNestedRelated({'two_pages_back': '1'}, queryset=qs)
        f2 = PageFilterWithAliasedNestedRelated({'two_pages_back': '2'}, queryset=qs)
        f3 = PageFilterWithAliasedNestedRelated({'two_pages_back': '3'}, queryset=qs)
        f4 = PageFilterWithAliasedNestedRelated({'two_pages_back': '4'}, queryset=qs)

        self.assertQuerysetEqual(f1.qs, [3], lambda p: p.pk)
        self.assertQuerysetEqual(f2.qs, [4], lambda p: p.pk)
        self.assertQuerysetEqual(f3.qs, [], lambda p: p.pk)
        self.assertQuerysetEqual(f4.qs, [], lambda p: p.pk)

    def test_relatedfilter_different_name(self):
        # Test the name filter on the related UserFilter set.
        GET = {
            'author__name': 'user2',
        }
        f = NoteFilterWithRelatedDifferentName(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        note = list(f.qs)[0]
        self.assertEqual(note.title, "Hello Test 4")

    def test_double_relation_filter(self):
        GET = {
            'note__author__username__endswith': 'user2'
        }
        f = PostFilter(GET, queryset=Post.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        post = list(f.qs)[0]
        self.assertEqual(post.content, "Test content in post 3")

    def test_triple_relation_filter(self):
        GET = {
            'post__note__author__username__endswith': 'user2'
        }
        f = CoverFilterWithRelated(GET, queryset=Cover.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        cover = list(f.qs)[0]
        self.assertEqual(cover.comment, "Cover 2")

    def test_indirect_recursive_relation(self):
        GET = {
            'a__b__name__endswith': '1'
        }
        f = CFilter(GET, queryset=C.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        c = list(f.qs)[0]
        self.assertEqual(c.title, "C1")

    def test_direct_recursive_relation(self):
        GET = {
            'best_friend__name__endswith': 'hn'
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "Mark")

    def test_m2m_relation(self):
        GET = {
            'tags__name__endswith': 'ark',
        }
        f = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.title, "First post")

        GET = {
            'tags__name__endswith': 'ouse',
        }
        f = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        self.assertEqual(len(list(f.qs)), 2)
        titles = set([person.title for person in f.qs])
        self.assertEqual(titles, set(["First post", "Second post"]))

    def test_nonexistent_related_field(self):
        """
        Invalid filter keys (including those on related filters) are invalid
        and should be ignored.

        Related: https://github.com/philipn/django-rest-framework-filters/issues/58
        """
        GET = {
            'author__nonexistent': 'foobar',
        }
        f = NoteFilterWithRelated(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

        GET = {
            'author__nonexistent__isnull': 'foobar',
        }
        f = NoteFilterWithRelated(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

    def test_related_filters_caching(self):
        filters = PostFilter.related_filters

        self.assertEqual(len(filters), 1)
        self.assertIn('note', filters)
        self.assertIn('_related_filters', PostFilter.__dict__)

        # subset should not use parent's cached related filters.
        PostSubset = PostFilter.get_subset(['title'])
        self.assertNotIn('_related_filters', PostSubset.__dict__)

        filters = PostSubset.related_filters
        self.assertIn('_related_filters', PostFilter.__dict__)

        self.assertEqual(len(filters), 0)

        # ensure subsets don't interact
        PostSubset = PostFilter.get_subset(['note'])
        self.assertNotIn('_related_filters', PostSubset.__dict__)

        filters = PostSubset.related_filters
        self.assertIn('_related_filters', PostFilter.__dict__)

        self.assertEqual(len(filters), 1)

    def test_relatedfilter_queryset_required(self):
        # Use a secure default queryset. Previous behavior was to use the default model
        # manager's `all()`, however this has the side effect of exposing related data.
        # The default behavior should not expose information, which requires users to
        # explicitly set the `queryset` argument.
        class NoteFilter(FilterSet):
            title = filters.CharFilter(field_name='title')
            author = filters.RelatedFilter(UserFilter, name='author')

            class Meta:
                model = Note
                fields = []

        GET = {'author': User.objects.get(username='user2').pk}
        f = NoteFilter(GET, queryset=Note.objects.all())

        with self.assertRaises(AssertionError) as excinfo:
            f.qs

        msg = str(excinfo.exception)
        self.assertEqual("Expected `.get_queryset()` for related filter 'NoteFilter.author' to return a `QuerySet`, but got `None`.", msg)

    def test_relatedfilter_request_is_passed(self):
        class RequestCheck(FilterSet):
            def __init__(self, *args, **kwargs):
                super(RequestCheck, self).__init__(*args, **kwargs)
                assert self.request is not None

            class Meta:
                model = User
                fields = ['username']

        class NoteFilter(FilterSet):
            author = filters.RelatedFilter(RequestCheck, name='author', queryset=User.objects.all())

            class Meta:
                model = Note
                fields = []

        GET = {'author__username': 'user2'}

        # should pass
        NoteFilter(GET, queryset=Note.objects.all(), request=object()).qs

    def test_validation(self):
        class F(PostFilter):
            pk = filters.NumberFilter(field_name='id')

        GET = {
            'note__author': 'foo',
            'pk': 'bar',
        }

        f = F(GET, queryset=Post.objects.all())
        self.assertQuerysetEqual(f.qs, Post.objects.none())
        self.assertFalse(f.form.is_valid())

        self.assertEqual(len(f.form.errors.keys()), 2)
        self.assertIn('note__author', f.form.errors)
        self.assertIn('pk', f.form.errors)


class MiscTests(TestCase):
    def test_multiwidget_incompatibility(self):
        Person.objects.create(name='A')

        # test django-filter functionality
        class PersonFilter(DFFilterSet):
            date_joined = filters.DateFromToRangeFilter(field_name='date_joined')

            class Meta:
                model = Person
                fields = ['date_joined']

        # Test from ... to 2016-01-01
        GET = {
            'date_joined_1': '2016-01-01',
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(f.qs.count(), 0)

        # test drf-filters caveat
        class PersonFilter(FilterSet):
            date_joined = filters.DateFromToRangeFilter(field_name='date_joined')

            class Meta:
                model = Person
                fields = ['date_joined']

        # Test from ... to 2016-01-01, failure case
        GET = {
            'date_joined_1': '2016-01-01',
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(f.qs.count(), 1)

        # Test from ... to 2016-01-01, "fix"
        GET = {
            'date_joined_1': '2016-01-01',
            'date_joined': '',
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(f.qs.count(), 0)
