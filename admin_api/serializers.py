from rest_framework import serializers
from tracks.models import Track
from albums.models import Album
from artists.models import Artist
from playlists.models import Playlist

class TrackAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = '__all__'

class AlbumAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = '__all__'

class ArtistAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'

class PlaylistAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = '__all__' 