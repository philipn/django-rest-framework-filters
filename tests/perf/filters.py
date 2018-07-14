
from django_filters import FilterSet as DFFilterSet

from rest_framework_filters import filters
from rest_framework_filters.filterset import FilterSet as DRFFilterSet

from ..testapp.models import Note, User


# df-filters
class NoteFilterWithExplicitRelated(DFFilterSet):
    class Meta:
        model = Note
        fields = {
            'title': [
                'exact', 'contains', 'startswith', 'endswith',
                'iexact', 'icontains', 'istartswith', 'iendswith',
            ],
            'author__username': ['exact'],
        }


# drf-filters
class UserFilterWithAll(DRFFilterSet):
    username = filters.AutoFilter(lookups='__all__')

    class Meta:
        model = User
        fields = []


class NoteFilterWithRelatedAll(DRFFilterSet):
    title = filters.AutoFilter(lookups='__all__')
    author = filters.RelatedFilter(UserFilterWithAll, queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []
