
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime

from django.test import TestCase

from rest_framework_filters import filters

from .testapp.models import (
    User, Note, Post, Cover, Page, A, B, C, Person, Tag, BlogPost,
)

from .testapp.filters import (
    NoteFilterWithAll,
    UserFilter,
    # UserFilterWithAll,
    NoteFilterWithRelated,
    NoteFilterWithRelatedAll,
    NoteFilterWithRelatedAllDifferentFilterName,
    PostFilter,
    CoverFilterWithRelatedMethodFilter,
    CoverFilterWithRelated,
    # PageFilterWithRelated,
    TagFilter,
    BlogPostFilter,
    OrderedBlogPostFilter,
    BlogPostOverrideFilter,
    # UserFilterWithDifferentName,
    NoteFilterWithRelatedDifferentName,

    # AFilter,
    # BFilter,
    CFilter,
    PersonFilter,

    # AllLookupsPersonDateFilter,
    # ExplicitLookupsPersonDateFilter,
    # InSetLookupPersonIDFilter,
    # InSetLookupPersonNameFilter,
)


class TestFilterSets(TestCase):

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
        page1 = Page.objects.create(title="First page", content="First first.")
        Page.objects.create(title="Second page", content="Second second.", previous_page=page1)

        ################################
        # ManyToMany
        ################################
        t1 = Tag.objects.create(name="park")
        Tag.objects.create(name="lake")
        t3 = Tag.objects.create(name="house")

        blogpost = BlogPost.objects.create(title="First post", content="First")
        blogpost.tags = [t1, t3]

        blogpost = BlogPost.objects.create(title="Second post", content="Secon")
        blogpost.tags = [t3]

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
        f = PostFilter(GET, queryset=Post.objects.all())
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
        self.assertEqual(len(list(f)), 4)

        GET = {
            'author__nonexistent__isnull': 'foobar',
        }
        f = NoteFilterWithRelated(GET, queryset=Note.objects.all())
        self.assertEqual(len(list(f)), 4)

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


class GetFilterNameTests(TestCase):

    def test_regular_filter(self):
        name = UserFilter.get_filter_name('email')
        self.assertEqual('email', name)

    def test_exclusion_filter(self):
        name = UserFilter.get_filter_name('email!')
        self.assertEqual('email', name)

    def test_non_filter(self):
        name = UserFilter.get_filter_name('foobar')
        self.assertEqual(None, name)

    def test_related_filter(self):
        # 'exact' matches
        name = NoteFilterWithRelated.get_filter_name('author')
        self.assertEqual('author', name)

        # related attribute filters
        name = NoteFilterWithRelated.get_filter_name('author__email')
        self.assertEqual('author', name)

        # non-existent related filters should match, as it's the responsibility
        # of the related filterset to handle non-existent filters
        name = NoteFilterWithRelated.get_filter_name('author__foobar')
        self.assertEqual('author', name)

    def test_twice_removed_related_filter(self):
        class PostFilterWithDirectAuthor(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilterWithAll)

            class Meta:
                model = Post

        name = PostFilterWithDirectAuthor.get_filter_name('note__title')
        self.assertEqual('note', name)

        # 'exact' matches, preference more specific filter name, as less specific
        # filter may not have related access.
        name = PostFilterWithDirectAuthor.get_filter_name('note__author')
        self.assertEqual('note__author', name)

        # related attribute filters
        name = PostFilterWithDirectAuthor.get_filter_name('note__author__email')
        self.assertEqual('note__author', name)

        # non-existent related filters should match, as it's the responsibility
        # of the related filterset to handle non-existent filters
        name = PostFilterWithDirectAuthor.get_filter_name('note__author__foobar')
        self.assertEqual('note__author', name)

    def test_name_hiding(self):
        class PostFilterNameHiding(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilterWithAll)
            note2 = filters.RelatedFilter(NoteFilterWithAll)

            class Meta:
                model = Post

        name = PostFilterNameHiding.get_filter_name('note__author')
        self.assertEqual('note__author', name)

        name = PostFilterNameHiding.get_filter_name('note__title')
        self.assertEqual('note', name)

        name = PostFilterNameHiding.get_filter_name('note')
        self.assertEqual('note', name)

        name = PostFilterNameHiding.get_filter_name('note2')
        self.assertEqual('note2', name)

        name = PostFilterNameHiding.get_filter_name('note2__author')
        self.assertEqual('note2', name)


class GetRelatedFilterParamTests(TestCase):

    def test_regular_filter(self):
        name, param = NoteFilterWithRelated.get_related_filter_param('title')
        self.assertIsNone(name)
        self.assertIsNone(param)

    def test_related_filter_exact(self):
        name, param = NoteFilterWithRelated.get_related_filter_param('author')
        self.assertIsNone(name)
        self.assertIsNone(param)

    def test_related_filter_param(self):
        name, param = NoteFilterWithRelated.get_related_filter_param('author__email')
        self.assertEqual('author', name)
        self.assertEqual('email', param)

    def test_name_hiding(self):
        class PostFilterNameHiding(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilterWithAll)
            note2 = filters.RelatedFilter(NoteFilterWithAll)

            class Meta:
                model = Post

        name, param = PostFilterNameHiding.get_related_filter_param('note__author__email')
        self.assertEqual('note__author', name)
        self.assertEqual('email', param)

        name, param = PostFilterNameHiding.get_related_filter_param('note__title')
        self.assertEqual('note', name)
        self.assertEqual('title', param)

        name, param = PostFilterNameHiding.get_related_filter_param('note2__title')
        self.assertEqual('note2', name)
        self.assertEqual('title', param)

        name, param = PostFilterNameHiding.get_related_filter_param('note2__author')
        self.assertEqual('note2', name)
        self.assertEqual('author', param)


class FilterSubsetTests(TestCase):

    def test_get_subset(self):
        filterset_class = UserFilter.get_subset(['email'])

        # ensure that the class name is useful when debugging
        self.assertEqual(filterset_class.__name__, 'UserFilterSubset')

        # ensure that the FilterSet subset only contains the requested fields
        self.assertIn('email', filterset_class.base_filters)
        self.assertEqual(len(filterset_class.base_filters), 1)

    def test_related_subset(self):
        # related filters should only return the local RelatedFilter
        filterset_class = NoteFilterWithRelated.get_subset(['title', 'author__email'])

        self.assertIn('title', filterset_class.base_filters)
        self.assertIn('author', filterset_class.base_filters)
        self.assertEqual(len(filterset_class.base_filters), 2)

    def test_non_filter_subset(self):
        # non-filter params should be ignored
        filterset_class = NoteFilterWithRelated.get_subset(['foobar'])
        self.assertEqual(len(filterset_class.base_filters), 0)


class MethodFilterTests(TestCase):

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
        results = list(filterset)
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
        results = list(filterset)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].comment, "Cover 2")


class FilterOverrideTests(TestCase):

    def test_declared_filters(self):
        F = BlogPostOverrideFilter

        # explicitly declared filters SHOULD NOT be overridden
        self.assertIsInstance(
            F.base_filters['declared_publish_date__isnull'],
            filters.NumberFilter
        )

        # declared `AllLookupsFilter`s SHOULD generate filters that ARE overridden
        self.assertIsInstance(
            F.base_filters['all_declared_publish_date__isnull'],
            filters.BooleanFilter
        )

    def test_dict_declaration(self):
        F = BlogPostOverrideFilter

        # dictionary style declared filters SHOULD be overridden
        self.assertIsInstance(
            F.base_filters['publish_date__isnull'],
            filters.BooleanFilter
        )


class FilterExclusionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
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


class OrderTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        tag1 = Tag.objects.create(name='Tag 1')
        tag2 = Tag.objects.create(name='Tag 2')
        tag3 = Tag.objects.create(name='Something else entirely')

        cls.post1 = BlogPost.objects.create(title='Post 1', content='content 1')
        cls.post2 = BlogPost.objects.create(title='Post 2', content='content 2')

        cls.post1.tags = [tag1, tag2]
        cls.post2.tags = [tag3]

        cls.post_number = 2

    def test_order(self):
        """
        The number of results in the filterset is passed to a set
        because we may have non distinct results.
        """
        queryset = BlogPost.objects.all()
        filterset = OrderedBlogPostFilter({}, queryset=queryset)
        results = [post.id for post in filterset]
        self.assertEqual(len(set(results)), self.post_number)
        # assert default order by -id
        self.assertEqual(
            results[0],
            self.post2.id
        )

        GET = {
            'o': 'tags'
        }
        filterset = OrderedBlogPostFilter(GET, queryset=BlogPost.objects.all())
        results = set([post.id for post in filterset])
        self.assertEqual(
            len(results),
            self.post_number
        )

        GET = {
            'o': '-publish_date,tags__name,-id'
        }
        filterset = OrderedBlogPostFilter(GET, queryset=BlogPost.objects.all())
        results = set([post.id for post in filterset])
        self.assertEqual(
            len(results),
            self.post_number
        )

        GET = {
            'o': 'bad_field'
        }
        filterset = OrderedBlogPostFilter(GET, queryset=BlogPost.objects.all())
        results = [post.id for post in filterset]
        self.assertEqual(len(results), 0)
