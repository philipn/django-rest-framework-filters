from django_filters.rest_framework import backends as df_backends
from rest_framework import viewsets

from rest_framework_filters import backends as drf_backends

from ..testapp.models import Note
from .filters import NoteFilterWithExplicitRelated, NoteFilterWithRelatedAll
from .serializers import NoteSerializer


class DFNoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filter_backends = [df_backends.DjangoFilterBackend]
    filterset_class = NoteFilterWithExplicitRelated


class DRFFNoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filter_backends = [drf_backends.RestFrameworkFilterBackend]
    filterset_class = NoteFilterWithRelatedAll
