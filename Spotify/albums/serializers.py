from rest_framework import serializers
from .models import Album, Artist, Genre
from genres.serializers import GenreSerializer

class AlbumSerializer(serializers.ModelSerializer):
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    genres_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        source='genres',
        write_only=True,
        required=False,
    )
    tracks_count = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = '__all__'

    def get_tracks_count(self, obj):
        return obj.tracks.count() 