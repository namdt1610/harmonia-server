from rest_framework import serializers
from .models import Artist, Album, Track, Playlist

class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'

class AlbumSerializer(serializers.ModelSerializer):
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())

    class Meta:
        model = Album
        fields = '__all__'

class TrackSerializer(serializers.ModelSerializer):
    album = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), required=False)
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True)

    class Meta:
        model = Track
        fields = '__all__'
    
    def validate_duration(self, value):
        print(f"Duration value received: {value}")
        if value is None:
            raise serializers.ValidationError("Duration cannot be null.")
        try:
            return int(value) 
        except ValueError:
            raise serializers.ValidationError("Duration must be a valid number.")

class PlaylistSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    tracks = serializers.PrimaryKeyRelatedField(many=True, queryset=Track.objects.all(), required=False)

    class Meta:
        model = Playlist
        fields = '__all__'
