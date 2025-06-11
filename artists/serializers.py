from rest_framework import serializers
from .models import Artist

class ArtistSerializer(serializers.ModelSerializer):
    # Computed fields
    tracks_count = serializers.SerializerMethodField()
    albums_count = serializers.SerializerMethodField()
    
    # URL fields
    image_url = serializers.SerializerMethodField()
    
    # Timestamp fields
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Artist
        fields = [
            'id', 'name', 'bio', 'image', 'image_url',
            'tracks_count', 'albums_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['tracks_count', 'albums_count', 'created_at', 'updated_at']
        ref_name = 'ArtistSerializer'
    
    def validate_name(self, value):
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_tracks_count(self, obj):
        return obj.tracks.count()
    
    def get_albums_count(self, obj):
        return obj.albums.count() 