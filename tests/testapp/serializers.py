
from rest_framework import serializers

from .models import User, Note, Project, Task


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'is_staff', )


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ('pk', 'title', 'content', 'author', )


class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(max_length=30)

    class Meta:
        model = Project
        fields = ('id', 'name', )


class TaskSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.HyperlinkedRelatedField(
        queryset=Project.objects.all(),
        view_name='project-detail',
        required=False)

    class Meta:
        model = Task
        fields = ('id', 'project', )
