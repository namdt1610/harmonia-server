from rest_framework import serializers
from .models import Album, Artist
from genres.models import Genre
from genres.serializers import GenreSerializer
from django.utils import timezone

class AlbumSerializer(serializers.ModelSerializer):
    # Foreign key relationships
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())
    
    # Read-only fields for related objects
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    
    # Genre handling
    genres = GenreSerializer(many=True, read_only=True)
    genres_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        source='genres',
        write_only=True,
        required=False,
    )
    
    # Computed fields
    tracks_count = serializers.SerializerMethodField()
    
    # URL fields
    image_url = serializers.SerializerMethodField()
    
    # Timestamp fields
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Album
        fields = [
            'id', 'title', 'artist', 'artist_name',
            'genres', 'genres_ids', 'image', 'image_url',
            'description', 'release_date', 'tracks_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['tracks_count', 'created_at', 'updated_at']
        ref_name = 'AlbumSerializer'
    
    def validate_title(self, value):
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_release_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Release date cannot be in the future")
        return value
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_tracks_count(self, obj):
        return obj.tracks.count() 