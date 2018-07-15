import sys
import warnings

from django.test import TestCase
from django_filters.filters import BaseInFilter
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from rest_framework_filters import FilterSet, filters
from rest_framework_filters.filterset import FilterSetMetaclass

from .testapp.filters import NoteFilter, PostFilter, TagFilter, UserFilter
from .testapp.models import Note, Person, Post, Tag

factory = APIRequestFactory()


class limit_recursion:
    def __init__(self):
        self.original_limit = sys.getrecursionlimit()

    def __enter__(self):
        sys.setrecursionlimit(100)

    def __exit__(self, *args):
        sys.setrecursionlimit(self.original_limit)


class MetaclassTests(TestCase):

    def test_metamethods(self):
        functions = [
            'expand_auto_filters',
        ]

        for func in functions:
            with self.subTest(func=func):
                self.assertTrue(hasattr(UserFilter, func))
                self.assertFalse(hasattr(UserFilter(), func))


class AutoFilterTests(TestCase):
    """
    Test auto filter generation (`AutoFilter`, `RelatedFilter`, '__all__').
    """

    def test_autofilter_meta_fields_unmodified(self):
        # The FilterSetMetaclass temporarily modifies the `FilterSet._meta` when
        # processing auto filters. Ensure the `_meta` isn't permanently altered.
        f = []

        class F(FilterSet):
            id = filters.AutoFilter(lookups='__all__')

            class Meta:
                model = Note
                fields = f

        self.assertIs(F._meta.fields, f)

    def test_autofilter_replaced(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/118
        class F(FilterSet):
            id = filters.AutoFilter(lookups='__all__')

            class Meta:
                model = Note
                fields = []

        self.assertIsInstance(F.declared_filters['id'], filters.AutoFilter)
        self.assertIsInstance(F.base_filters['id'], filters.NumberFilter)

    def test_all_lookups_for_relation(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/84
        class F(FilterSet):
            class Meta:
                model = Note
                fields = {
                    'author': '__all__',
                }

        self.assertIsInstance(F.base_filters['author'], filters.ModelChoiceFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_autofilter_for_related_field(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/127
        class F(FilterSet):
            author = filters.AutoFilter(field_name='author__last_name', lookups='__all__')

            class Meta:
                model = Note
                fields = []

        self.assertIsInstance(F.base_filters['author'], filters.CharFilter)
        self.assertEqual(F.base_filters['author'].field_name, 'author__last_name')

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
        # ensure that related filter is compatible with AutoFilter lookups.
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter, lookups='__all__')

            class Meta:
                model = Note
                fields = []

        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_relatedfilter_lookups_default(self):
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter)

            class Meta:
                model = Note
                fields = []

        self.assertEqual(len([f for f in F.base_filters if f.startswith('author')]), 1)
        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)

    def test_relatedfilter_lookups_list(self):
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter, lookups=['in'])

            class Meta:
                model = Note
                fields = []

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

    def test_declared_filter_persistence_with_autofilter(self):
        # ensure that AutoFilter does not overwrite declared filters.
        f = filters.Filter()

        class F(FilterSet):
            id = filters.AutoFilter(lookups='__all__')
            id__in = f

            class Meta:
                model = Note
                fields = []

        self.assertIs(F.base_filters['id__in'], f)

    def test_alllookupsfilter_deprecation_warning(self):
        message = ("`AllLookupsFilter()` has been deprecated in "
                   "favor of `AutoFilter(lookups='__all__')`.")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')

            class F(FilterSet):
                field = filters.AllLookupsFilter()

        self.assertEqual(len(w), 1)
        self.assertEqual(str(w[0].message), message)
        self.assertIs(w[0].category, DeprecationWarning)


class GetParamFilterNameTests(TestCase):

    def test_regular_filter(self):
        name = UserFilter.get_param_filter_name('email')
        self.assertEqual('email', name)

    def test_exclusion_filter(self):
        name = UserFilter.get_param_filter_name('email!')
        self.assertEqual('email', name)

    def test_non_filter(self):
        name = UserFilter.get_param_filter_name('foobar')
        self.assertEqual(None, name)

    def test_related_filter(self):
        # 'exact' matches
        name = NoteFilter.get_param_filter_name('author')
        self.assertEqual('author', name)

        # related attribute filters
        name = NoteFilter.get_param_filter_name('author__email')
        self.assertEqual('author', name)

        # non-existent related filters should match, as it's the responsibility
        # of the related filterset to handle non-existent filters
        name = NoteFilter.get_param_filter_name('author__foobar')
        self.assertEqual('author', name)

    def test_twice_removed_related_filter(self):
        class PostFilterWithDirectAuthor(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilter)

            class Meta:
                model = Post
                fields = []

        name = PostFilterWithDirectAuthor.get_param_filter_name('note__title')
        self.assertEqual('note', name)

        # 'exact' matches, preference more specific filter name, as less specific
        # filter may not have related access.
        name = PostFilterWithDirectAuthor.get_param_filter_name('note__author')
        self.assertEqual('note__author', name)

        # related attribute filters
        name = PostFilterWithDirectAuthor.get_param_filter_name('note__author__email')
        self.assertEqual('note__author', name)

        # non-existent related filters should match, as it's the responsibility
        # of the related filterset to handle non-existent filters
        name = PostFilterWithDirectAuthor.get_param_filter_name('note__author__foobar')
        self.assertEqual('note__author', name)

    def test_name_hiding(self):
        class PostFilterNameHiding(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilter)
            note2 = filters.RelatedFilter(NoteFilter)

            class Meta:
                model = Post
                fields = []

        name = PostFilterNameHiding.get_param_filter_name('note__author')
        self.assertEqual('note__author', name)

        name = PostFilterNameHiding.get_param_filter_name('note__title')
        self.assertEqual('note', name)

        name = PostFilterNameHiding.get_param_filter_name('note')
        self.assertEqual('note', name)

        name = PostFilterNameHiding.get_param_filter_name('note2')
        self.assertEqual('note2', name)

        name = PostFilterNameHiding.get_param_filter_name('note2__author')
        self.assertEqual('note2', name)


class GetRelatedFilterParamTests(TestCase):

    def test_regular_filter(self):
        name, param = NoteFilter.get_related_filter_param('title')
        self.assertIsNone(name)
        self.assertIsNone(param)

    def test_related_filter_exact(self):
        name, param = NoteFilter.get_related_filter_param('author')
        self.assertIsNone(name)
        self.assertIsNone(param)

    def test_related_filter_param(self):
        name, param = NoteFilter.get_related_filter_param('author__email')
        self.assertEqual('author', name)
        self.assertEqual('email', param)

    def test_name_hiding(self):
        class PostFilterNameHiding(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilter)
            note2 = filters.RelatedFilter(NoteFilter)

            class Meta:
                model = Post
                fields = []

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


class GetFilterSubsetTests(TestCase):

    def test_get_subset(self):
        filter_subset = UserFilter.get_filter_subset(['email'])

        # ensure that the FilterSet subset only contains the requested fields
        self.assertIn('email', filter_subset)
        self.assertEqual(len(filter_subset), 1)

    def test_related_subset(self):
        # related filters should only return the local RelatedFilter
        filter_subset = NoteFilter.get_filter_subset(['title', 'author', 'author__email'])

        self.assertIn('title', filter_subset)
        self.assertIn('author', filter_subset)
        self.assertEqual(len(filter_subset), 2)

    def test_non_filter_subset(self):
        # non-filter params should be ignored
        filter_subset = NoteFilter.get_filter_subset(['foobar'])
        self.assertEqual(len(filter_subset), 0)

    def test_metaclass_inheritance(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/132
        class SubMetaclass(FilterSetMetaclass):
            pass

        class SubFilterSet(FilterSet, metaclass=SubMetaclass):
            pass

        class NoteFilter(SubFilterSet):
            author = filters.RelatedFilter(UserFilter)

            class Meta:
                model = Note
                fields = ['title', 'content']

        filter_subset = NoteFilter.get_filter_subset(['author', 'content'])

        # ensure that the FilterSet subset only contains the requested fields
        self.assertIn('author', filter_subset)
        self.assertIn('content', filter_subset)
        self.assertEqual(len(filter_subset), 2)


class DisableSubsetTests(TestCase):
    class F(FilterSet):
        class Meta:
            model = Note
            fields = ['author']

    def test_unbound_subset(self):
        F = self.F.disable_subset()
        self.assertEqual(list(F().filters), ['author'])

    def test_bound_subset(self):
        F = self.F.disable_subset()
        self.assertEqual(list(F({}).filters), ['author'])
        self.assertEqual(list(F({'author': ''}).filters), ['author'])

    def test_duplicate_disable(self):
        F = self.F.disable_subset().disable_subset()
        self.assertEqual(list(F({}).filters), ['author'])

    def test_subset_form(self):
        # test that subsetted forms only have provided fields
        F = self.F
        self.assertEqual(list(F({}).form.fields), [])
        self.assertEqual(list(F({'author': ''}).form.fields), ['author'])

    def test_subset_disabled_form(self):
        # test that subset disabled forms have all fields
        F = self.F.disable_subset()
        self.assertEqual(list(F({}).form.fields), ['author'])
        self.assertEqual(list(F({'author': ''}).form.fields), ['author'])


class OverrideFiltersTests(TestCase):

    def test_bound(self):
        f = PostFilter({})

        with f.override_filters():
            self.assertEqual(len(f.filters), 0)

    def test_not_bound(self):
        f = PostFilter(None)

        with f.override_filters():
            self.assertEqual(len(f.filters), 0)

    def test_subset_disabled(self):
        f = PostFilter.disable_subset()(None)

        with f.override_filters():
            # The number of filters varies by Django version
            self.assertGreater(len(f.filters), 30)


class FilterExclusionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        t1 = Tag.objects.create(name='Tag 1')
        t2 = Tag.objects.create(name='Tag 2')
        t3 = Tag.objects.create(name='Something else entirely')

        p1 = Post.objects.create(title='Post 1', content='content 1')
        p2 = Post.objects.create(title='Post 2', content='content 2')

        p1.tags.set([t1, t2])
        p2.tags.set([t3])

    def test_exclude_property(self):
        """
        Ensure that the filter is set to exclude
        """
        GET = {
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        requested_filters = filterset.request_filters

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
        requested_filters = filterset.request_filters

        self.assertFalse(requested_filters['name__contains'].exclude)
        self.assertTrue(requested_filters['name__contains!'].exclude)

    def test_related_exclude(self):
        GET = {
            'tags__name__contains!': 'Tag',
        }

        filterset = PostFilter(GET, queryset=Post.objects.all())
        requested_filters = filterset.request_filters

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

        filterset = PostFilter(GET, queryset=Post.objects.all())
        results = [r.title for r in filterset.qs]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Post 2')

    def test_exclude_and_request_interaction(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/171
        request = APIView().initialize_request(factory.get('/?tags__name__contains!=Tag'))
        filterset = PostFilter(request.query_params, request=request, queryset=Post.objects.all())

        try:
            with limit_recursion():
                qs = filterset.qs
        except RuntimeError:
            self.fail('Recursion limit reached')

        results = [r.title for r in qs]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Post 2')
