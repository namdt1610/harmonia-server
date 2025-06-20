from rest_framework import serializers
from .models import Track, Album, Artist, Genre
from genres.serializers import GenreSerializer
from favorites.models import Favorite

class TrackSerializer(serializers.ModelSerializer):
    # Foreign key relationships
    album = serializers.PrimaryKeyRelatedField(queryset=Album.objects.all(), required=False, allow_null=True)
    artist = serializers.PrimaryKeyRelatedField(queryset=Artist.objects.all())
    
    # Read-only fields for related objects
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True)
    
    # Genre handling
    genres = GenreSerializer(many=True, read_only=True)
    genres_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(),
        many=True,
        source='genres',
        write_only=True,
        required=False,
    )
    
    # URL fields
    file_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    # Computed fields
    is_favorite = serializers.SerializerMethodField()
    
    # Statistics fields
    play_count = serializers.IntegerField(read_only=True)
    download_count = serializers.IntegerField(read_only=True)
    
    # Timestamp fields
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'artist_name',
            'album', 'album_title', 'genres', 'genres_ids',
            'duration', 'file', 'file_url', 'image', 'image_url', 
            'lyrics', 'is_downloadable', 'is_favorite',
            'play_count', 'download_count',
            'created_at', 'updated_at'
        ]
        ref_name = 'TrackSerializer'
        read_only_fields = ['play_count', 'download_count', 'created_at', 'updated_at']
    
    def validate_title(self, value):
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_duration(self, value):
        if value is None:
            raise serializers.ValidationError("Duration cannot be null.")
        try:
            duration = int(value)
            if duration < 0:
                raise serializers.ValidationError("Duration must be a positive number.")
            return duration
        except ValueError:
            raise serializers.ValidationError("Duration must be a valid number.")
    
    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("File is required")
        # Check file extension
        if not value.name.lower().endswith(('.mp3', '.wav', '.ogg')):
            raise serializers.ValidationError("Only audio files (mp3, wav, ogg) are allowed")
        return value
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if not request:
            return False
            
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
            
        if not hasattr(obj, 'id'):
            return False
            
        try:
            return Favorite.objects.filter(
                user=user, 
                track_id=obj.id
            ).exists()
        except Exception as e:
            print(f"Error checking favorite status: {e}")
            return False 