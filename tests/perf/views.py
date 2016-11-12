
from rest_framework import viewsets
from rest_framework import filters as df_backends
from rest_framework_filters import backends

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
    filter_backends = (backends.DjangoFilterBackend, )
    filter_class = NoteFilterWithRelatedAll
