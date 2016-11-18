
import django_filters
from rest_framework_filters import filters
from rest_framework_filters.filters import RelatedFilter, AllLookupsFilter
from rest_framework_filters.filterset import FilterSet, LOOKUP_SEP


from .models import (
    User, Note, Post, Cover, Page, A, B, C, Person, Tag, BlogPost,
)


class DFUserFilter(django_filters.FilterSet):
    email = filters.CharFilter(name='email')

    class Meta:
        model = User
        fields = '__all__'


class NoteFilterWithAll(FilterSet):
    title = AllLookupsFilter(name='title')

    class Meta:
        model = Note
        fields = []


class UserFilter(FilterSet):
    username = filters.CharFilter(name='username')
    email = filters.CharFilter(name='email')
    last_login = filters.AllLookupsFilter()
    is_active = filters.BooleanFilter(name='is_active')

    class Meta:
        model = User
        fields = []


class UserFilterWithAll(FilterSet):
    username = AllLookupsFilter(name='username')
    email = filters.CharFilter(name='email')

    class Meta:
        model = User
        fields = []


class NoteFilterWithRelated(FilterSet):
    title = filters.CharFilter(name='title')
    author = RelatedFilter(UserFilter, name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class NoteFilterWithRelatedAll(FilterSet):
    title = filters.CharFilter(name='title')
    author = RelatedFilter(UserFilterWithAll, name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class NoteFilterWithRelatedAllDifferentFilterName(FilterSet):
    title = filters.CharFilter(name='title')
    writer = RelatedFilter(UserFilterWithAll, name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class PostFilter(FilterSet):
    # Used for Related filter and Filter.method regression tests
    note = RelatedFilter(NoteFilterWithRelatedAll, name='note', queryset=Note.objects.all())
    date_published = filters.AllLookupsFilter()
    is_published = filters.BooleanFilter(name='date_published', method='filter_is_published')

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
    comment = filters.CharFilter(name='comment')
    post = RelatedFilter(PostFilter, name='post', queryset=Post.objects.all())

    class Meta:
        model = Cover
        fields = []


class CoverFilterWithRelated(FilterSet):
    comment = filters.CharFilter(name='comment')
    post = RelatedFilter(PostFilter, name='post', queryset=Post.objects.all())

    class Meta:
        model = Cover
        fields = []


class PageFilterWithRelated(FilterSet):
    title = filters.CharFilter(name='title')
    previous_page = RelatedFilter(PostFilter, name='previous_page', queryset=Post.objects.all())

    class Meta:
        model = Page
        fields = []


class TagFilter(FilterSet):
    name = AllLookupsFilter(name='name')

    class Meta:
        model = Tag
        fields = []


class BlogPostFilter(FilterSet):
    title = filters.CharFilter(name='title')
    tags = RelatedFilter(TagFilter, name='tags', queryset=Tag.objects.all())

    class Meta:
        model = BlogPost
        fields = []


class UserFilterWithDifferentName(FilterSet):
    name = filters.CharFilter(name='username')

    class Meta:
        model = User
        fields = []


class NoteFilterWithRelatedDifferentName(FilterSet):
    author = RelatedFilter(UserFilterWithDifferentName, name='author')

    class Meta:
        model = Note
        fields = []


#############################################################
# Recursive filtersets
#############################################################
class AFilter(FilterSet):
    title = filters.CharFilter(name='title')
    b = RelatedFilter('tests.testapp.filters.BFilter', name='b')

    class Meta:
        model = A
        fields = []


class CFilter(FilterSet):
    title = filters.CharFilter(name='title')
    a = RelatedFilter(AFilter, name='a')

    class Meta:
        model = C
        fields = []


class BFilter(FilterSet):
    name = AllLookupsFilter(name='name')
    c = RelatedFilter(CFilter, name='c')

    class Meta:
        model = B
        fields = []


class PersonFilter(FilterSet):
    name = AllLookupsFilter(name='name')
    best_friend = RelatedFilter('tests.testapp.filters.PersonFilter', name='best_friend', queryset=Person.objects.all())

    class Meta:
        model = Person
        fields = []


#############################################################
# Extensions to django_filter fields for DRF.
#############################################################
class AllLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(name='date_joined')
    time_joined = AllLookupsFilter(name='time_joined')
    datetime_joined = AllLookupsFilter(name='datetime_joined')

    class Meta:
        model = Person
        fields = []


class ExplicitLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(name='date_joined')
    time_joined = AllLookupsFilter(name='time_joined')
    datetime_joined = AllLookupsFilter(name='datetime_joined')

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
    declared_publish_date__isnull = filters.NumberFilter(name='publish_date', lookup_expr='isnull')
    all_declared_publish_date = filters.AllLookupsFilter(name='publish_date')

    class Meta:
        model = BlogPost
        fields = {'publish_date': '__all__', }
