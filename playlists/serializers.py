from rest_framework import serializers
from .models import Playlist, Track
from tracks.serializers import TrackSerializer

class PlaylistSerializer(serializers.ModelSerializer):
    # Track relationships
    tracks = TrackSerializer(many=True, read_only=True)
    tracks_ids = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.all(),
        many=True,
        source='tracks',
        write_only=True,
        required=False,
    )
    
    # Computed fields
    user_name = serializers.CharField(source='user.username', read_only=True)
    tracks_count = serializers.SerializerMethodField()
    
    # URL fields
    image_url = serializers.SerializerMethodField()
    
    # Timestamp fields
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'description', 'user', 'user_name',
            'tracks', 'tracks_ids', 'tracks_count', 'is_public',
            'image', 'image_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'tracks_count', 'created_at', 'updated_at']
        ref_name = 'PlaylistSerializer'
    
    def validate_name(self, value):
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def get_tracks_count(self, obj):
        return obj.tracks.count()
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data) 