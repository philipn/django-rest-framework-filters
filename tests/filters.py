
from rest_framework_filters import filters
from rest_framework_filters.filters import RelatedFilter, AllLookupsFilter
from rest_framework_filters.filterset import FilterSet, LOOKUP_SEP


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
    last_login = filters.AllLookupsFilter()
    is_active = filters.BooleanFilter(name='is_active')

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


class PostFilter(FilterSet):
    # Used for Related filter and MethodFilter tests
    note = RelatedFilter(NoteFilterWithRelatedAll, name='note')
    date_published = filters.AllLookupsFilter()
    is_published = filters.MethodFilter()

    class Meta:
        model = Post

    def filter_is_published(self, name, qs, value):
        """
        `is_published` is based on the actual `date_published`.
        If the publishing date is null, then the post is not published.
        """
        # convert value to boolean
        null = value.lower() != 'true'

        # The lookup name will end with `is_published`, but could be
        # preceded by a related lookup path.
        if LOOKUP_SEP in name:
            rel, _ = name.rsplit(LOOKUP_SEP, 1)
            name = LOOKUP_SEP.join([rel, 'date_published__isnull'])
        else:
            name = 'date_published__isnull'

        return qs.filter(**{name: null})


class CoverFilterWithRelatedMethodFilter(FilterSet):
    comment = filters.CharFilter(name='comment')
    post = RelatedFilter(PostFilter, name='post')

    class Meta:
        model = Cover


class CoverFilterWithRelated(FilterSet):
    comment = filters.CharFilter(name='comment')
    post = RelatedFilter(PostFilter, name='post')

    class Meta:
        model = Cover


class PageFilterWithRelated(FilterSet):
    title = filters.CharFilter(name='title')
    previous_page = RelatedFilter(PostFilter, name='previous_page')

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


class BlogPostOverrideFilter(FilterSet):
    declared_publish_date__isnull = filters.NumberFilter(name='publish_date', lookup_type='isnull')
    all_declared_publish_date = filters.AllLookupsFilter(name='publish_date')

    class Meta:
        model = BlogPost
        fields = {'publish_date': filters.ALL_LOOKUPS, }
