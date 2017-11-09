
from rest_framework import serializers

from .models import User, Note, Application, Release


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'is_staff', )


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ('pk', 'title', 'content', 'author', )


class ApplicationSerializer(serializers.ModelSerializer):
    releases = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Application
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = '__all__'
