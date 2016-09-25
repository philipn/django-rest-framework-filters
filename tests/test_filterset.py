
from __future__ import absolute_import
from __future__ import unicode_literals

from django.test import TestCase

from rest_framework_filters.compat import set_many
from rest_framework_filters import filters, FilterSet
from django_filters.filters import BaseInFilter

from .testapp.models import (
    Note, Post, Person, Tag, BlogPost,
)

from .testapp.filters import (
    UserFilter,
    NoteFilterWithAll,
    NoteFilterWithRelated,
    PostFilter,
    TagFilter,
    BlogPostFilter,
    BlogPostOverrideFilter,
)


class LookupsFilterTests(TestCase):
    """
    Test basic filter construction for `AllLookupsFilter`, '__all__', and `RelatedFilter.lookups`.
    """

    def test_alllookupsfilter_replaced(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/118
        class F(FilterSet):
            id = filters.AllLookupsFilter()

            class Meta:
                model = Note

        self.assertIsInstance(F.declared_filters['id'], filters.AllLookupsFilter)
        self.assertIsInstance(F.base_filters['id'], filters.NumberFilter)

    def test_alllookupsfilter_for_relation(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/84
        class F(FilterSet):
            class Meta:
                model = Note
                fields = {
                    'author': '__all__',
                }

        self.assertIsInstance(F.base_filters['author'], filters.ModelChoiceFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_relatedfilter_combined_with__all__(self):
        # ensure that related filter is compatible with __all__ lookups.
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter)

            class Meta:
                model = Note
                fields = {
                    'author': '__all__',
                }

        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_relatedfilter_lookups(self):
        # ensure that related filter is compatible with __all__ lookups.
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter, lookups='__all__')

            class Meta:
                model = Note

        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_relatedfilter_lookups_list(self):
        # ensure that related filter is compatible with __all__ lookups.
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter, lookups=['in'])

            class Meta:
                model = Note

        self.assertEqual(len([f for f in F.base_filters if f.startswith('author')]), 2)
        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_declared_filter_persistence_with__all__(self):
        # ensure that __all__ does not overwrite declared filters.
        f = filters.Filter()

        class F(FilterSet):
            name = f

            class Meta:
                model = Person
                fields = {'name': '__all__'}

        self.assertIs(F.base_filters['name'], f)

    def test_declared_filter_persistence_with_alllookupsfilter(self):
        # ensure that AllLookupsFilter does not overwrite declared filters.
        f = filters.Filter()

        class F(FilterSet):
            id = filters.AllLookupsFilter()
            id__in = f

            class Meta:
                model = Note

        self.assertIs(F.base_filters['id__in'], f)


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

        set_many(p1, 'tags', [t1, t2])
        set_many(p2, 'tags', [t3])

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
        results = [r.name for r in filterset.qs]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Something else entirely')

    def test_filter_and_exclusion_results(self):
        GET = {
            'name__contains': 'Tag',
            'name__contains!': '2',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        results = [r.name for r in filterset.qs]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Tag 1')

    def test_related_exclusion_results(self):
        GET = {
            'tags__name__contains!': 'Tag',
        }

        filterset = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        results = [r.title for r in filterset.qs]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Post 2')
