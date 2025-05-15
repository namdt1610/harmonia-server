from rest_framework import serializers
from .models import UserActivity
from tracks.serializers import TrackSerializer
from playlists.serializers import PlaylistSerializer

class UserActivitySerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    playlist = PlaylistSerializer(read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ('user', 'timestamp') 