from django.test import TestCase
from django_filters import FilterSet as DFFilterSet

from rest_framework_filters import FilterSet, filters

from .testapp.filters import (
    AccountFilter, CFilter, CoverFilter, CustomerFilter, NoteFilter, NoteFilterWithAlias,
    NoteFilterWithRelatedAlias, PageFilter, PersonFilter, PostFilter, UserFilter,
)
from .testapp.models import (
    A, Account, B, C, Cover, Customer, Note, Page, Person, Post, Tag, User,
)


class LocalTagFilter(FilterSet):
    class Meta:
        model = Tag
        fields = []


class AutoFilterTests(TestCase):

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

    def test_all_lookups(self):
        # Test __iendswith
        GET = {'title__iendswith': '2'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Test 2")

        # Test __contains
        GET = {'title__contains': 'Test'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

        # Test that the default exact filter works
        GET = {'title': 'Hello Test 3'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 3")

    def test_autofilter_with_mixin(self):
        # Mixin FilterSets should not error when no model is provided. See:
        # https://github.com/philipn/django-rest-framework-filters/issues/82
        class Mixin(FilterSet):
            title = filters.AutoFilter(lookups='__all__')

        class Actual(Mixin):
            class Meta:
                model = Note
                fields = []

        class Subclass(Actual):
            class Meta:
                model = Note
                fields = []

        GET = {'title__contains': 'Hello'}
        f = Actual(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 2)

        GET = {'title__contains': 'Hello'}
        f = Subclass(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 2)


class RelatedFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        ########################################################################
        # Create users #########################################################
        user1 = User.objects.create(username="user1", email="user1@example.org")
        user2 = User.objects.create(username="user2", email="user2@example.org")

        ########################################################################
        # Create notes #########################################################
        note1 = Note.objects.create(title="Test 1",
                                    content="Test content 1",
                                    author=user1)
        note2 = Note.objects.create(title="Test 2",
                                    content="Test content 2",
                                    author=user1)
        Note.objects.create(title="Hello Test 3",
                            content="Test content 3",
                            author=user1)
        note4 = Note.objects.create(title="Hello Test 4",
                                    content="Test content 4",
                                    author=user2)

        ########################################################################
        # Create posts #########################################################
        post1 = Post.objects.create(note=note1, content="Test content in post 1")
        post2 = Post.objects.create(note=note2, content="Test content in post 2")
        post3 = Post.objects.create(note=note4, content="Test content in post 3")

        ########################################################################
        # Create covers ########################################################
        Cover.objects.create(post=post1, comment="Cover 1")
        Cover.objects.create(post=post3, comment="Cover 2")

        ########################################################################
        # Create pages #########################################################
        Page.objects.create(title="First page",
                            content="First first.")
        Page.objects.create(title="Second page",
                            content="Second second.",
                            previous_page_id=1)
        Page.objects.create(title="Third page",
                            content="Third third.",
                            previous_page_id=2)
        Page.objects.create(title="Fourth page",
                            content="Fourth fourth.",
                            previous_page_id=3)

        ########################################################################
        # ManyToMany ###########################################################
        t1 = Tag.objects.create(name="park")
        Tag.objects.create(name="lake")
        t3 = Tag.objects.create(name="house")

        post1.tags.set([t1, t3])
        post3.tags.set([t3])

        ########################################################################
        # ManyToMany distinct ##################################################
        t4 = Tag.objects.create(name="test1")
        t5 = Tag.objects.create(name="test2")

        post2.tags.set([t4, t5])

        ########################################################################
        # Recursive relations ##################################################
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

        ########################################################################
        # to_field relations ###################################################
        c1 = Customer.objects.create(name='Bob Jones', ssn='111111111', dob='1990-01-01')
        c2 = Customer.objects.create(name='Sue Jones', ssn='222222222', dob='1990-01-01')

        Account.objects.create(customer=c1, type='c', name='Bank 1 checking')
        Account.objects.create(customer=c1, type='s', name='Bank 1 savings')
        Account.objects.create(customer=c2, type='c', name='Bank 1 checking 1')
        Account.objects.create(customer=c2, type='c', name='Bank 1 checking 2')
        Account.objects.create(customer=c2, type='s', name='Bank 2 savings')

    def test_relatedfilter(self):
        # Test that the default exact filter works
        GET = {'author': User.objects.get(username='user2').pk}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {'author__username': 'user2'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

    def test_relatedfilter_for_related_all_lookups(self):
        # ensure that filters work for AutoFilter across a RelatedFilter.

        # Test that the default exact filter works
        GET = {'author': User.objects.get(username='user2').pk}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        note = list(f.qs)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {'author__username': 'user2'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'author__username__endswith': '2'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'author__username__endswith': '1'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 3)

        GET = {'author__username__contains': 'user'}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

    def test_relatedfilter_for_related_all_lookups_and_different_filter_name(self):
        # Test that the default exact filter works
        GET = {
            'writer': User.objects.get(username='user2').pk,
        }
        f = NoteFilterWithAlias(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        note = list(f.qs)[0]
        self.assertEqual(note.title, "Hello Test 4")

        # Test the username filter on the related UserFilter set.
        GET = {'writer__username': 'user2'}
        f = NoteFilterWithAlias(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'writer__username__endswith': '2'}
        f = NoteFilterWithAlias(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        self.assertEqual(list(f.qs)[0].title, "Hello Test 4")

        GET = {'writer__username__endswith': '1'}
        f = NoteFilterWithAlias(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 3)

        GET = {'writer__username__contains': 'user'}
        f = NoteFilterWithAlias(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

    def test_relatedfilter_for_aliased_nested_relationships(self):
        qs = Page.objects.order_by('pk')

        f1 = PageFilter({'two_pages_back': '1'}, queryset=qs)
        f2 = PageFilter({'two_pages_back': '2'}, queryset=qs)
        f3 = PageFilter({'two_pages_back': '3'}, queryset=qs)
        f4 = PageFilter({'two_pages_back': '4'}, queryset=qs)

        self.assertQuerysetEqual(f1.qs, [3], lambda p: p.pk)
        self.assertQuerysetEqual(f2.qs, [4], lambda p: p.pk)
        self.assertQuerysetEqual(f3.qs, [], lambda p: p.pk)
        self.assertQuerysetEqual(f4.qs, [], lambda p: p.pk)

    def test_relatedfilter_different_name(self):
        # Test the name filter on the related UserFilter set.
        GET = {
            'author__name': 'user2',
        }
        f = NoteFilterWithRelatedAlias(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        note = list(f.qs)[0]
        self.assertEqual(note.title, "Hello Test 4")

    def test_double_relation_filter(self):
        GET = {
            'note__author__username__endswith': 'user2',
        }
        f = PostFilter(GET, queryset=Post.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        post = list(f.qs)[0]
        self.assertEqual(post.content, "Test content in post 3")

    def test_triple_relation_filter(self):
        GET = {
            'post__note__author__username__endswith': 'user2',
        }
        f = CoverFilter(GET, queryset=Cover.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        cover = list(f.qs)[0]
        self.assertEqual(cover.comment, "Cover 2")

    def test_indirect_recursive_relation(self):
        GET = {
            'a__b__name__endswith': '1',
        }
        f = CFilter(GET, queryset=C.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        c = list(f.qs)[0]
        self.assertEqual(c.title, "C1")

    def test_direct_recursive_relation(self):
        # see: https://github.com/philipn/django-rest-framework-filters/issues/333
        GET = {
            'best_friend': 1,
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "Mark")

    def test_direct_recursive_relation__lookup(self):
        GET = {
            'best_friend__name__endswith': 'hn',
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.name, "Mark")

    def test_m2m_relation(self):
        GET = {
            'tags__name__endswith': 'ark',
        }
        f = PostFilter(GET, queryset=Post.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        p = list(f.qs)[0]
        self.assertEqual(p.content, "Test content in post 1")

        GET = {
            'tags__name__endswith': 'ouse',
        }
        f = PostFilter(GET, queryset=Post.objects.all())
        self.assertEqual(len(list(f.qs)), 2)
        contents = {post.content for post in f.qs}
        self.assertEqual(contents, {'Test content in post 1', 'Test content in post 3'})

    def test_m2m_distinct(self):
        GET = {
            'tags__name__startswith': 'test',
        }
        f = PostFilter(GET, queryset=Post.objects.all())
        self.assertEqual(len(list(f.qs)), 1)
        contents = {post.content for post in f.qs}
        self.assertEqual(contents, {'Test content in post 2'})

    def test_nonexistent_related_field(self):
        # Invalid filter keys (including those on related filters) should be ignored.
        # Related: https://github.com/philipn/django-rest-framework-filters/issues/58
        GET = {
            'author__nonexistent': 'foobar',
        }
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

        GET = {
            'author__nonexistent__isnull': 'foobar',
        }
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 4)

    def test_related_filters_inheritance(self):
        class ChildFilter(PostFilter):
            foo = filters.RelatedFilter(NoteFilter, field_name='note')

        self.assertEqual(
            ['author', 'note', 'tags'],
            list(PostFilter.related_filters),
        )
        self.assertEqual(
            ['author', 'note', 'tags', 'foo'],
            list(ChildFilter.related_filters),
        )

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
        msg = "Expected `.get_queryset()` for related filter 'NoteFilter.author' " \
              "to return a `QuerySet`, but got `None`."
        with self.assertRaisesMessage(AssertionError, msg):
            NoteFilter(GET, queryset=Note.objects.all())

    def test_relatedfilter_request_is_passed(self):
        called = False

        class RequestCheck(FilterSet):
            def __init__(self, *args, **kwargs):
                super(RequestCheck, self).__init__(*args, **kwargs)
                assert self.request is not None

                nonlocal called
                called = True

            class Meta:
                model = User
                fields = ['username']

        class NoteFilter(FilterSet):
            author = filters.RelatedFilter(RequestCheck, queryset=User.objects.all())

            class Meta:
                model = Note
                fields = []

        GET = {'author__username': 'user2'}

        # should pass
        NoteFilter(GET, queryset=Note.objects.all(), request=object()).qs
        self.assertTrue(called)

    def test_validation(self):
        class F(PostFilter):
            pk = filters.NumberFilter(field_name='id')

        GET = {
            'note__author': 'foo',
            'pk': 'bar',
        }

        f = F(GET, queryset=Post.objects.all())
        self.assertEqual(f.qs.count(), 3)
        self.assertFalse(f.is_valid())

        self.assertEqual(len(f.form.errors.keys()), 2)
        self.assertIn('note__author', f.form.errors)
        self.assertIn('pk', f.form.errors)

    def test_relative_filterset_path(self):
        # Test that RelatedFilter can import FilterSets by name from its parent's module
        class PostFilter(FilterSet):
            tags = filters.RelatedFilter('LocalTagFilter', queryset=Tag.objects.all())

        f = PostFilter({'tags': ''}, queryset=Post.objects.all())
        f = f.filters['tags'].filterset

        self.assertEqual(f.__module__, 'tests.test_filtering')
        self.assertEqual(f.__name__, 'LocalTagFilter')

    def test_empty_param_name(self):
        GET = {'': 'foo', 'author': User.objects.get(username='user2').pk}
        f = NoteFilter(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f.qs)), 1)

    def test_to_field_forwards_relation(self):
        GET = {'customer__name': 'Bob Jones'}
        f = AccountFilter(GET)
        self.assertEqual(len(list(f.qs)), 2)

    def test_to_field_reverse_relation(self):
        # Note: pending #99, this query should ideally return 2 distinct results
        GET = {'accounts__type': 'c'}
        f = CustomerFilter(GET)
        self.assertEqual(len(list(f.qs)), 3)


class AnnotationTests(TestCase):
    # TODO: these tests should somehow assert that the annotation method is
    # called, but the qs isn't easily due to chaining mockable.

    @classmethod
    def setUpTestData(cls):
        author1 = User.objects.create(username='author1', email='author1@example.org')
        author2 = User.objects.create(username='author2', email='author2@example.org')
        Post.objects.create(author=author1, content='Post 1', publish_date='2018-01-01')
        Post.objects.create(author=author2, content='Post 2', publish_date=None)

    def test_annotation(self):
        f = PostFilter(
            {'is_published': 'true'},
            queryset=Post.objects.all(),
        )

        self.assertEqual([p.content for p in f.qs], ['Post 1'])

    def test_related_annotation(self):
        f = UserFilter(
            {'posts__is_published': 'true'},
            queryset=User.objects.all(),
        )

        self.assertEqual([a.username for a in f.qs], ['author1'])


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
            'date_joined_before': '2016-01-01',
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
            'date_joined_before': '2016-01-01',
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(f.qs.count(), 1)

        # Test from ... to 2016-01-01, "fix"
        GET = {
            'date_joined_before': '2016-01-01',
            'date_joined': '',
        }
        f = PersonFilter(GET, queryset=Person.objects.all())
        self.assertEqual(f.qs.count(), 0)
