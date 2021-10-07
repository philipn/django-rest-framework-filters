import sys
import unittest
import warnings

import django_filters
from django.test import TestCase
from django_filters.filters import BaseInFilter
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from rest_framework_filters import FilterSet, filters
from rest_framework_filters.filterset import FilterSetMetaclass, SubsetDisabledMixin

from .testapp.filters import (
    AFilter, NoteFilter, NoteFilterWithAlias, PersonFilter, PostFilter, TagFilter,
    UserFilter,
)
from .testapp.models import Note, Person, Post, Tag, User

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
            'get_auto_filters',
            'expand_auto_filter',
        ]

        for func in functions:
            with self.subTest(func=func):
                self.assertTrue(hasattr(UserFilter, func))
                self.assertFalse(hasattr(UserFilter(), func))


class AutoFilterTests(TestCase):
    # Test auto filter generation (`AutoFilter`, `RelatedFilter`, '__all__').

    def test_autofilter_not_declared(self):
        # AutoFilter is not an actual Filter subclass
        f = filters.AutoFilter(lookups=['exact'])

        class F(FilterSet):
            id = f

        self.assertEqual(F.auto_filters, {'id': f})
        self.assertEqual(F.declared_filters, {})

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
            id = filters.AutoFilter(lookups=['exact'])

            class Meta:
                model = Note
                fields = []

        self.assertEqual(list(F.base_filters), ['id'])
        self.assertIsInstance(F.base_filters['id'], filters.NumberFilter)
        self.assertEqual(F.base_filters['id'].lookup_expr, 'exact')

    def test_autofilter_noop(self):
        class F(FilterSet):
            id = filters.AutoFilter(lookups=[])

            class Meta:
                model = Note
                fields = []

        self.assertEqual(F.base_filters, {})

    def test_autofilter_with_mixin(self):
        class Mixin(FilterSet):
            title = filters.AutoFilter(lookups=['exact'])

        class Actual(Mixin):
            class Meta:
                model = Note
                fields = []

        class Subclass(Actual):
            class Meta:
                model = Note
                fields = []

        base_filters = {name: type(f) for name, f in Mixin.base_filters.items()}
        self.assertEqual(base_filters, {})

        base_filters = {name: type(f) for name, f in Actual.base_filters.items()}
        self.assertEqual(base_filters, {'title': filters.CharFilter})

        base_filters = {name: type(f) for name, f in Subclass.base_filters.items()}
        self.assertEqual(base_filters, {'title': filters.CharFilter})

    def test_autofilter_doesnt_expand_declared(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/234
        class F(FilterSet):
            pk = filters.AutoFilter(field_name='id', lookups=['exact'])
            individual = filters.CharFilter()

            class Meta:
                model = Note
                fields = []

        base_filters = {name: type(f) for name, f in F.base_filters.items()}
        self.assertEqual(base_filters, {
            'individual': filters.CharFilter,
            'pk': filters.NumberFilter,
        })

    @unittest.skipIf(django_filters.VERSION < (2, 2), 'requires django-filter 2.2')
    def test_autofilter_invalid_field(self):
        msg = "'Meta.fields' must not contain non-model field names: xyz"
        with self.assertRaisesMessage(TypeError, msg):
            class F(FilterSet):
                pk = filters.AutoFilter(field_name='xyz', lookups=['exact'])

                class Meta:
                    model = Note
                    fields = []

    @unittest.skipIf(django_filters.VERSION < (2, 2), 'requires django-filter 2.2')
    def test_all_lookups_invalid_field(self):
        msg = "'Meta.fields' must not contain non-model field names: xyz"
        with self.assertRaisesMessage(TypeError, msg):
            class F(FilterSet):
                class Meta:
                    model = Note
                    fields = {
                        'xyz': '__all__',
                    }

    def test_relatedfilter_doesnt_expand_declared(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/234
        class F(FilterSet):
            posts = filters.RelatedFilter(
                PostFilter,
                field_name='post',
                lookups=['exact'],
            )

            class Meta:
                model = User
                fields = []

        base_filters = {name: type(f) for name, f in F.base_filters.items()}
        self.assertEqual(base_filters, {
            'posts': filters.RelatedFilter,
        })

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


class GetRelatedFiltersetsTests(TestCase):

    def test_not_bound(self):
        filtersets = UserFilter().get_related_filtersets()

        self.assertEqual(len(filtersets), 0)

    def test_not_related_filter(self):
        filtersets = NoteFilter({
            'title': 'foo',
        }).get_related_filtersets()

        self.assertEqual(len(filtersets), 0)

    def test_exact(self):
        filtersets = NoteFilter({
            'author': 'bob',
        }).get_related_filtersets()

        self.assertEqual(len(filtersets), 1)
        self.assertIsInstance(filtersets['author'], UserFilter)

    def test_filterset(self):
        filtersets = NoteFilter({
            'author__username': 'bob',
        }).get_related_filtersets()

        self.assertEqual(len(filtersets), 1)
        self.assertIsInstance(filtersets['author'], UserFilter)

    def test_filterset_alias(self):
        filtersets = NoteFilterWithAlias({
            'writer__username': 'bob',
        }).get_related_filtersets()

        self.assertEqual(len(filtersets), 1)
        self.assertIsInstance(filtersets['writer'], UserFilter)

    def test_filterset_twice_removed(self):
        filtersets = PostFilter({
            'note__author__username': 'bob',
        }).get_related_filtersets()

        self.assertEqual(len(filtersets), 1)
        self.assertIsInstance(filtersets['note'], NoteFilter)

        filtersets = filtersets['note'].get_related_filtersets()

        self.assertEqual(len(filtersets), 1)
        self.assertIsInstance(filtersets['author'], UserFilter)

    def test_filterset_multiple_filters(self):
        filtersets = PostFilter({
            'note__foo': 'bob', 'tags__bar': 'joe',
        }).get_related_filtersets()

        self.assertEqual(len(filtersets), 2)
        self.assertIsInstance(filtersets['note'], NoteFilter)
        self.assertIsInstance(filtersets['tags'], TagFilter)


class GetParamFilterNameTests(TestCase):

    def test_regular_filter(self):
        name = UserFilter.get_param_filter_name('email')
        self.assertEqual('email', name)

    def test_exclusion_filter(self):
        name = UserFilter.get_param_filter_name('email!')
        self.assertEqual('email', name)

    def test_non_filter(self):
        name = UserFilter.get_param_filter_name('foobar')
        self.assertIsNone(name)

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

    def test_relationship_regular_filter(self):
        name = UserFilter.get_param_filter_name('author__email', rel='author')
        self.assertEqual('email', name)

    def test_recursive_self_filter(self):
        name = PersonFilter.get_param_filter_name('best_friend')
        self.assertEqual('best_friend', name)

    def test_related_recursive_self_filter(self):
        # see: https://github.com/philipn/django-rest-framework-filters/issues/333
        name = PersonFilter.get_param_filter_name('best_friend', rel='best_friend')
        self.assertIsNone(name)

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
            note2 = filters.RelatedFilter(NoteFilter, field_name='note')

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


class GetFilterSubsetTests(TestCase):

    class NoteFilter(FilterSet):
        # A simpler version of NoteFilter that doesn't use autofilter expansion
        title = filters.CharFilter()
        author = filters.RelatedFilter(UserFilter)

        class Meta:
            model = Note
            fields = []

    def test_get_subset(self):
        filter_subset = self.NoteFilter.get_filter_subset(['title'])

        # ensure that the FilterSet subset only contains the requested fields
        self.assertEqual(list(filter_subset), ['title'])

    def test_related_subset(self):
        # related filters should only return the local RelatedFilter
        filter_subset = ['title', 'author', 'author__email']
        filter_subset = self.NoteFilter.get_filter_subset(filter_subset)

        self.assertEqual(list(filter_subset), ['title', 'author'])

    def test_non_filter_subset(self):
        # non-filter params should be ignored
        filter_subset = self.NoteFilter.get_filter_subset(['foobar'])
        self.assertEqual(list(filter_subset), [])

    def test_subset_ordering(self):
        # sanity check ordering of base filters
        filter_subset = ['title', 'author']
        filter_subset = [f for f in self.NoteFilter.base_filters if f in filter_subset]
        self.assertEqual(list(filter_subset), ['title', 'author'])

        # ensure that the ordering of the subset is the same as the base filters
        filter_subset = self.NoteFilter.get_filter_subset(['title', 'author'])
        self.assertEqual(list(filter_subset), ['title', 'author'])

        # ensure reverse argument order does not change subset ordering
        filter_subset = self.NoteFilter.get_filter_subset(['author', 'title'])
        self.assertEqual(list(filter_subset), ['title', 'author'])

        # ensure related filters do not change subset ordering
        filter_subset = ['author__email', 'author', 'title']
        filter_subset = self.NoteFilter.get_filter_subset(filter_subset)
        self.assertEqual(list(filter_subset), ['title', 'author'])

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
        self.assertEqual(list(filter_subset), ['content', 'author'])


class DisableSubsetTests(TestCase):
    class F(FilterSet):
        class Meta:
            model = Note
            fields = ['author']

    def test_unbound_subset(self):
        F = self.F.disable_subset()
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(F().filters), ['author'])

    def test_bound_subset(self):
        F = self.F.disable_subset()
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(F({}).filters), ['author'])
        self.assertEqual(list(F({'author': ''}).filters), ['author'])

    def test_duplicate_disable(self):
        F = self.F.disable_subset().disable_subset()
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(F({}).filters), ['author'])

    def test_subset_form(self):
        # test that subset-enabled forms only have provided fields
        F = self.F
        self.assertFalse(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(F({}).form.fields), [])
        self.assertEqual(list(F({'author': ''}).form.fields), ['author'])

    def test_subset_disabled_form(self):
        # test that subset-disabled forms have all fields
        F = self.F.disable_subset()
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(F({}).form.fields), ['author'])
        self.assertEqual(list(F({'author': ''}).form.fields), ['author'])


class DisableSubsetRecursiveTests(TestCase):

    def test_depth0(self):
        F = AFilter.disable_subset(depth=0)
        f = F()

        # 0-depth disabled
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), ['title', 'b'])

        # 1-depth not disabled
        F = f.filters['b'].filterset
        f = f.related_filtersets['b']
        self.assertFalse(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), [])

    def test_depth1(self):
        F = AFilter.disable_subset(depth=1)
        f = F()

        # 0-depth disabled
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), ['title', 'b'])

        # 1-depth disabled
        F = f.filters['b'].filterset
        f = f.related_filtersets['b']
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), ['name', 'c'])

        # 2-depth not disabled
        F = f.filters['c'].filterset
        f = f.related_filtersets['c']
        self.assertFalse(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), [])

    def test_depth2(self):
        F = original = AFilter.disable_subset(depth=2)
        f = F()

        # 0-depth disabled
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), ['title', 'b'])

        # 1-depth disabled
        F = f.filters['b'].filterset
        f = f.related_filtersets['b']
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), ['name', 'c'])

        # 2-depth disabled
        F = f.filters['c'].filterset
        f = f.related_filtersets['c']
        self.assertTrue(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), ['title', 'a'])

        # 3-depth not disabled
        F = f.filters['a'].filterset
        f = f.related_filtersets['a']
        self.assertFalse(issubclass(F, SubsetDisabledMixin))
        self.assertEqual(list(f.filters), [])

        # relationship has looped, nested A is *not* original/disabled A.
        self.assertIsNot(original, F)
        self.assertTrue(issubclass(original, F))


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
        # Ensure that the filter is set to exclude
        GET = {
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())

        self.assertTrue(filterset.filters['name__contains!'].exclude)

    def test_filter_and_exclude(self):
        # Ensure that both the filter and exclusion filter are available
        GET = {
            'name__contains': 'Tag',
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())

        self.assertFalse(filterset.filters['name__contains'].exclude)
        self.assertTrue(filterset.filters['name__contains!'].exclude)

    def test_related_exclude(self):
        GET = {
            'tags__name__contains!': 'Tag',
        }

        filterset = PostFilter(GET, queryset=Post.objects.all())
        filterset = filterset.related_filtersets['tags']

        self.assertTrue(filterset.filters['name__contains!'].exclude)

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
        filterset = PostFilter(
            request.query_params,
            request=request,
            queryset=Post.objects.all(),
        )

        try:
            with limit_recursion():
                qs = filterset.qs
        except RuntimeError:
            self.fail('Recursion limit reached')

        results = [r.title for r in qs]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Post 2')
