from rest_framework import serializers
from .models import Playlist, Track
from tracks.serializers import TrackSerializer

class PlaylistSerializer(serializers.ModelSerializer):
    tracks = TrackSerializer(many=True, read_only=True)
    tracks_ids = serializers.PrimaryKeyRelatedField(
        queryset=Track.objects.all(),
        many=True,
        source='tracks',
        write_only=True,
        required=False,
    )
    user_name = serializers.CharField(source='user.username', read_only=True)
    tracks_count = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = '__all__'
        read_only_fields = ('user',)

    def get_tracks_count(self, obj):
        return obj.tracks.count()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data) 