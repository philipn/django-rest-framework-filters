
from rest_framework import serializers

from ..testapp.models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['pk', 'title', 'content', 'author']
