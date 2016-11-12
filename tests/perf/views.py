
from rest_framework import viewsets
from django_filters.rest_framework import backends as df_backends
from rest_framework_filters import backends as drf_backends

from ..testapp.models import Note
from .serializers import NoteSerializer
from .filters import NoteFilterWithExplicitRelated, NoteFilterWithRelatedAll


class DFNoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filter_backends = (df_backends.DjangoFilterBackend, )
    filter_class = NoteFilterWithExplicitRelated


class DRFFNoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filter_backends = (drf_backends.DjangoFilterBackend, )
    filter_class = NoteFilterWithRelatedAll
