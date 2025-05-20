from rest_framework import serializers
from .models import Queue, QueueTrack
from music.serializers import TrackSerializer

class QueueTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    class Meta:
        model = QueueTrack
        fields = ['id', 'track', 'order', 'added_at']

class QueueSerializer(serializers.ModelSerializer):
    tracks = QueueTrackSerializer(source='queuetrack_set', many=True, read_only=True)
    class Meta:
        model = Queue
        fields = ['id', 'user', 'tracks', 'created_at', 'updated_at'] 