from rest_framework import serializers
from .models import Queue, QueueTrack
from tracks.serializers import TrackSerializer

class QueueTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    class Meta:
        model = QueueTrack
        fields = ['id', 'track', 'order', 'added_at']

class QueueSerializer(serializers.ModelSerializer):
    tracks = serializers.SerializerMethodField()
    
    class Meta:
        model = Queue
        fields = ['id', 'user', 'tracks', 'current_index', 'created_at', 'updated_at']
    
    def get_tracks(self, obj):
        # Only return tracks that haven't been soft deleted, ordered by order field
        queue_tracks = obj.queuetrack_set.filter(is_deleted=False).order_by('order')
        return QueueTrackSerializer(queue_tracks, many=True).data 