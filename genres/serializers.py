from rest_framework import serializers
from .models import Genre
from django.db.models import Count

class GenreSerializer(serializers.ModelSerializer):
    # Computed fields
    tracks_count = serializers.SerializerMethodField()
    albums_count = serializers.SerializerMethodField()
    
    # Timestamp fields
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Genre
        fields = [
            'id', 'name', 'description',
            'tracks_count', 'albums_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['tracks_count', 'albums_count', 'created_at', 'updated_at']
        ref_name = 'GenreSerializer'
    
    def validate_name(self, value):
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def get_tracks_count(self, obj):
        return obj.tracks.count()
    
    def get_albums_count(self, obj):
        # Count unique albums through tracks
        return obj.tracks.values('album').distinct().count() 