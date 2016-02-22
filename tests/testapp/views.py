
from rest_framework import viewsets
from rest_framework_filters import backends

from .models import User, Note
from .serializers import UserSerializer, NoteSerializer
from .filters import UserFilterWithAll, NoteFilterWithRelatedAll


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (backends.DjangoFilterBackend, )
    filter_class = UserFilterWithAll


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    filter_backends = (backends.DjangoFilterBackend, )
    filter_class = NoteFilterWithRelatedAll
