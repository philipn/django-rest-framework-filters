
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


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
