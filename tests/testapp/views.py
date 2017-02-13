
from rest_framework import viewsets
from rest_framework_filters import backends

from .models import User, Note, Project, Task
from .serializers import UserSerializer, NoteSerializer, ProjectSerializer, TaskSerializer
from .filters import DFUserFilter, UserFilterWithAll, NoteFilterWithRelatedAll, ProjectFilter, TaskFilter


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


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    filter_backends = (backends.DjangoFilterBackend,)
    filter_class = ProjectFilter
    queryset = Project.objects.all()
    model = Task


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    filter_backends = (backends.DjangoFilterBackend,)
    filter_class = TaskFilter
    queryset = Task.objects.all()
    model = Project
