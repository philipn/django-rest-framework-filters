
from rest_framework import serializers

from .models import Note, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['pk', 'username', 'email', 'is_staff']


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['pk', 'title', 'content', 'author']
