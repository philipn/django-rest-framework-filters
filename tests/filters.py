
from rest_framework_filters import filters
from rest_framework_filters.filters import RelatedFilter, AllLookupsFilter
from rest_framework_filters.filterset import FilterSet


from .models import (
    User, Note, Post, Cover, Page, A, B, C, Person, Tag, BlogPost,
)


class NoteFilterWithAll(FilterSet):
    title = AllLookupsFilter(name='title')

    class Meta:
        model = Note


class UserFilter(FilterSet):
    username = filters.CharFilter(name='username')
    email = filters.CharFilter(name='email')

    class Meta:
        model = User


class UserFilterWithAll(FilterSet):
    username = AllLookupsFilter(name='username')
    email = filters.CharFilter(name='email')

    class Meta:
        model = User


class NoteFilterWithRelated(FilterSet):
    title = filters.CharFilter(name='title')
    author = RelatedFilter(UserFilter, name='author')

    class Meta:
        model = Note


class NoteFilterWithRelatedAll(FilterSet):
    title = filters.CharFilter(name='title')
    author = RelatedFilter(UserFilterWithAll, name='author')

    class Meta:
        model = Note


class NoteFilterWithRelatedAllDifferentFilterName(FilterSet):
    title = filters.CharFilter(name='title')
    writer = RelatedFilter(UserFilterWithAll, name='author')

    class Meta:
        model = Note


class PostFilterWithRelated(FilterSet):
    note = RelatedFilter(NoteFilterWithRelatedAll, name='note')

    class Meta:
        model = Post


class CoverFilterWithRelated(FilterSet):
    comment = filters.CharFilter(name='comment')
    post = RelatedFilter(PostFilterWithRelated, name='post')

    class Meta:
        model = Cover


class PageFilterWithRelated(FilterSet):
    title = filters.CharFilter(name='title')
    previous_page = RelatedFilter(PostFilterWithRelated, name='previous_page')

    class Meta:
        model = Page


class TagFilter(FilterSet):
    name = AllLookupsFilter(name='name')

    class Meta:
        model = Tag


class BlogPostFilter(FilterSet):
    title = filters.CharFilter(name='title')
    tags = RelatedFilter(TagFilter, name='tags')

    class Meta:
        model = BlogPost


class UserFilterWithDifferentName(FilterSet):
    name = filters.CharFilter(name='username')

    class Meta:
        model = User


class NoteFilterWithRelatedDifferentName(FilterSet):
    author = RelatedFilter(UserFilterWithDifferentName, name='author')

    class Meta:
        model = Note


#############################################################
# Recursive filtersets
#############################################################
class AFilter(FilterSet):
    title = filters.CharFilter(name='title')
    b = RelatedFilter('tests.filters.BFilter', name='b')

    class Meta:
        model = A


class CFilter(FilterSet):
    title = filters.CharFilter(name='title')
    a = RelatedFilter(AFilter, name='a')

    class Meta:
        model = C


class BFilter(FilterSet):
    name = AllLookupsFilter(name='name')
    c = RelatedFilter(CFilter, name='c')

    class Meta:
        model = B


class PersonFilter(FilterSet):
    name = AllLookupsFilter(name='name')
    best_friend = RelatedFilter('tests.filters.PersonFilter', name='best_friend')

    class Meta:
        model = Person


#############################################################
# Extensions to django_filter fields for DRF.
#############################################################
class AllLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(name='date_joined')
    time_joined = AllLookupsFilter(name='time_joined')
    datetime_joined = AllLookupsFilter(name='datetime_joined')

    class Meta:
        model = Person


class ExplicitLookupsPersonDateFilter(FilterSet):
    date_joined = AllLookupsFilter(name='date_joined')
    time_joined = AllLookupsFilter(name='time_joined')
    datetime_joined = AllLookupsFilter(name='datetime_joined')

    class Meta:
        model = Person


class InSetLookupPersonIDFilter(FilterSet):
    pk = AllLookupsFilter('id')

    class Meta:
        model = Person


class InSetLookupPersonNameFilter(FilterSet):
    name = AllLookupsFilter('name')

    class Meta:
        model = Person
