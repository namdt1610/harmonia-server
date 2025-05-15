from rest_framework import serializers
from .models import Track, Album, Artist, Genre
from genres.serializers import GenreSerializer
from albums.serializers import AlbumSerializer
from artists.serializers import ArtistSerializer

class TrackSerializer(serializers.ModelSerializer):
    album = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), required=False)
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    genres_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        source='genres',
        write_only=True,
        required=False,
    )

    class Meta:
        model = Track
        fields = '__all__'
    
    def validate_duration(self, value):
        if value is None:
            raise serializers.ValidationError("Duration cannot be null.")
        try:
            return int(value) 
        except ValueError:
            raise serializers.ValidationError("Duration must be a valid number.") 