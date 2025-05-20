from rest_framework import serializers
from .models import Favorite
from tracks.serializers import TrackSerializer
from artists.serializers import ArtistSerializer
from albums.serializers import AlbumSerializer
from playlists.serializers import PlaylistSerializer

class FavoriteSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    artist = ArtistSerializer(read_only=True)
    album = AlbumSerializer(read_only=True)
    playlist = PlaylistSerializer(read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Favorite
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

    def validate(self, data):
        # Ensure exactly one content object is set
        content_objects = [data.get('track'), data.get('artist'), data.get('album'), data.get('playlist')]
        if content_objects.count(None) != 3:
            raise serializers.ValidationError("Exactly one content object must be set")
        
        # Set content_type based on the set object
        if data.get('track'):
            data['content_type'] = 'track'
        elif data.get('artist'):
            data['content_type'] = 'artist'
        elif data.get('album'):
            data['content_type'] = 'album'
        elif data.get('playlist'):
            data['content_type'] = 'playlist'
            
        return data 