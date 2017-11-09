
from rest_framework import viewsets
from rest_framework_filters import backends

from .models import User, Note, Application, Release
from .serializers import UserSerializer, NoteSerializer, ApplicationSerializer, ReleaseSerializer
from .filters import DFUserFilter, UserFilterWithAll, NoteFilterWithRelatedAll, ApplicationFilter, ReleaseFilter


class DFUserViewSet(viewsets.ModelViewSet):
    # used to test compatibility with the drf-filters backend
    # with standard django-filter FilterSets.
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (backends.DjangoFilterBackend, )
    filter_class = DFUserFilter


class FilterFieldsUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (backends.DjangoFilterBackend, )
    filter_fields = {
        'username': '__all__',
    }


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


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    filter_class = ApplicationFilter


class ReleaseViewSet(viewsets.ModelViewSet):
    queryset = Release.objects.all()
    serializer_class = ReleaseSerializer
    filter_class = ReleaseFilter
