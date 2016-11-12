
from django_filters import FilterSet as DFFilterSet
from rest_framework_filters import filters
from rest_framework_filters.filterset import FilterSet as DRFFilterSet

from ..testapp.models import User, Note


# df-filters
class NoteFilterWithExplicitRelated(DFFilterSet):
    class Meta:
        model = Note
        fields = {
            'author__username': ['exact'],
        }


# drf-filters
class UserFilterWithAll(DRFFilterSet):
    username = filters.AllLookupsFilter()

    class Meta:
        model = User
        fields = []


class NoteFilterWithRelatedAll(DRFFilterSet):
    title = filters.AllLookupsFilter()
    author = filters.RelatedFilter(UserFilterWithAll)

    class Meta:
        model = Note
        fields = []
