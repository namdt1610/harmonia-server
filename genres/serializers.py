from rest_framework import serializers
from .models import Genre

class GenreSerializer(serializers.ModelSerializer):
    tracks_count = serializers.SerializerMethodField()
    albums_count = serializers.SerializerMethodField()

    class Meta:
        model = Genre
        fields = '__all__'

    def get_tracks_count(self, obj):
        return obj.tracks.count()

    def get_albums_count(self, obj):
        return obj.albums.count() 