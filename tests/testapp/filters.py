
import django_filters

from rest_framework_filters import filters
from rest_framework_filters.filters import AllLookupsFilter, RelatedFilter
from rest_framework_filters.filterset import LOOKUP_SEP, FilterSet

from .models import (
    A, B, BlogPost, C, Cover, Note, Page, Person, Post, Tag, User,
)


class DFUserFilter(django_filters.FilterSet):
    email = filters.CharFilter(field_name='email')

    class Meta:
        model = User
        fields = '__all__'


class NoteFilterWithAll(FilterSet):
    title = AllLookupsFilter(field_name='title')

    class Meta:
        model = Note
        fields = []


class UserFilter(FilterSet):
    username = filters.CharFilter(field_name='username')
    email = filters.CharFilter(field_name='email')
    last_login = filters.AllLookupsFilter()
    is_active = filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = User
        fields = []


class UserFilterWithAll(FilterSet):
    username = AllLookupsFilter(field_name='username')
    email = filters.CharFilter(field_name='email')

    class Meta:
        model = User
        fields = []


class NoteFilterWithRelated(FilterSet):
    title = filters.CharFilter(field_name='title')
    author = RelatedFilter(UserFilter, field_name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class NoteFilterWithRelatedAll(FilterSet):
    title = filters.CharFilter(field_name='title')
    author = RelatedFilter(UserFilterWithAll, field_name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class NoteFilterWithRelatedAllDifferentFilterName(FilterSet):
    title = filters.CharFilter(field_name='title')
    writer = RelatedFilter(UserFilterWithAll, field_name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class PostFilter(FilterSet):
    # Used for Related filter and Filter.method regression tests
    note = RelatedFilter(NoteFilterWithRelatedAll, field_name='note', queryset=Note.objects.all())
    date_published = filters.AllLookupsFilter()
    is_published = filters.BooleanFilter(field_name='date_published', method='filter_is_published')

    class Meta:
        model = Post
        fields = []

    def filter_is_published(self, qs, name, value):
        """
        `is_published` is based on the actual `date_published`.
        If the publishing date is null, then the post is not published.
        """
        isnull = not value
        lookup_expr = LOOKUP_SEP.join([name, 'isnull'])

        return qs.filter(**{lookup_expr: isnull})


class CoverFilterWithRelatedMethodFilter(FilterSet):
    comment = filters.CharFilter(field_name='comment')
    post = RelatedFilter(PostFilter, field_name='post', queryset=Post.objects.all())

    class Meta:
        model = Cover
        fields = []


class CoverFilterWithRelated(FilterSet):
    comment = filters.CharFilter(field_name='comment')
    post = RelatedFilter(PostFilter, field_name='post', queryset=Post.objects.all())

    class Meta:
        model = Cover
        fields = []


class PageFilterWithRelated(FilterSet):
    title = filters.CharFilter(field_name='title')
    previous_page = RelatedFilter(PostFilter, field_name='previous_page', queryset=Post.objects.all())

    class Meta:
        model = Page
        fields = []


class PageFilterWithAliasedNestedRelated(FilterSet):
    title = filters.CharFilter(field_name='title')
    two_pages_back = RelatedFilter(PostFilter, field_name='previous_page__previous_page', queryset=Page.objects.all())

    class Meta:
        model = Page
        fields = []


class TagFilter(FilterSet):
    name = AllLookupsFilter(field_name='name')

    class Meta:
        model = Tag
        fields = []


class BlogPostFilter(FilterSet):
    title = filters.CharFilter(field_name='title')
    tags = RelatedFilter(TagFilter, field_name='tags', queryset=Tag.objects.all())

    class Meta:
        model = BlogPost
        fields = []


class UserFilterWithDifferentName(FilterSet):
    name = filters.CharFilter(field_name='username')

    class Meta:
        model = User
        fields = []


class NoteFilterWithRelatedDifferentName(FilterSet):
    author = RelatedFilter(UserFilterWithDifferentName, field_name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


#############################################################
# Recursive filtersets
#############################################################
class AFilter(FilterSet):
    title = filters.CharFilter(field_name='title')
    b = RelatedFilter('tests.testapp.filters.BFilter', field_name='b', queryset=B.objects.all())

    class Meta:
        model = A
        fields = []


class CFilter(FilterSet):
    title = filters.CharFilter(field_name='title')
    a = RelatedFilter(AFilter, field_name='a', queryset=A.objects.all())

    class Meta:
        model = C
        fields = []


class BFilter(FilterSet):
    name = AllLookupsFilter(field_name='name')
    c = RelatedFilter(CFilter, field_name='c', queryset=C.objects.all())

    class Meta:
        model = B
        fields = []


class PersonFilter(FilterSet):
    name = AllLookupsFilter(field_name='name')
    best_friend = RelatedFilter(
        'tests.testapp.filters.PersonFilter',
        field_name='best_friend',
        queryset=Person.objects.all(),
    )

    class Meta:
        model = Person
        fields = []


#############################################################
# Extensions to django_filter fields for DRF.
#############################################################
class AllLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(field_name='date_joined')
    time_joined = AllLookupsFilter(field_name='time_joined')
    datetime_joined = AllLookupsFilter(field_name='datetime_joined')

    class Meta:
        model = Person
        fields = []


class ExplicitLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(field_name='date_joined')
    time_joined = AllLookupsFilter(field_name='time_joined')
    datetime_joined = AllLookupsFilter(field_name='datetime_joined')

    class Meta:
        model = Person
        fields = []


class InSetLookupPersonIDFilter(FilterSet):
    pk = AllLookupsFilter('id')

    class Meta:
        model = Person
        fields = []


class InSetLookupPersonNameFilter(FilterSet):
    name = AllLookupsFilter('name')

    class Meta:
        model = Person
        fields = []


class BlogPostOverrideFilter(FilterSet):
    declared_publish_date__isnull = filters.NumberFilter(field_name='publish_date', lookup_expr='isnull')
    all_declared_publish_date = filters.AllLookupsFilter(field_name='publish_date')

    class Meta:
        model = BlogPost
        fields = {'publish_date': '__all__', }
