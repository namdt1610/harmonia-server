from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Queue, QueueTrack
from .serializers import QueueSerializer, QueueTrackSerializer
from music.models import Track
from playlists.models import Playlist
from albums.models import Album

class QueueViewSet(viewsets.ModelViewSet):
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Queue.objects.filter(user=self.request.user)

    def _cleanup_queues(self, user):
        """Clean up duplicate queues for a user, keeping only the most recent one"""
        queues = Queue.objects.filter(user=user).order_by('-id')
        if queues.count() > 1:
            # Keep the most recent queue
            latest_queue = queues.first()
            # Delete all other queues
            Queue.objects.filter(user=user).exclude(id=latest_queue.id).delete()
            return latest_queue
        return queues.first()

    @action(detail=False, methods=['get'], url_path='current-queue')
    def current_queue(self, request):
        # Clean up any duplicate queues first
        queue = self._cleanup_queues(request.user)
        if not queue:
            queue, _ = Queue.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(queue)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add-track/(?P<track_id>\\d+)')
    def add_track(self, request, track_id=None):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        track = Track.objects.get(pk=track_id)
        order = queue.queuetrack_set.count()
        QueueTrack.objects.create(queue=queue, track=track, order=order)
        return Response({'status': 'track added to queue'})

    @action(detail=False, methods=['post'], url_path='remove-track/(?P<track_id>\\d+)')
    def remove_track(self, request, track_id=None):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        QueueTrack.objects.filter(queue=queue, track_id=track_id).delete()
        return Response({'status': 'track removed from queue'})

    @action(detail=False, methods=['post'], url_path='add-playlist/(?P<playlist_id>\\d+)')
    def add_playlist(self, request, playlist_id=None):
        # Clean up existing queue first
        Queue.objects.filter(user=request.user).delete()
        # Create new queue and add playlist tracks
        queue = Queue.objects.create(user=request.user)
        playlist = Playlist.objects.get(pk=playlist_id)
        for idx, track in enumerate(playlist.tracks.all()):
            QueueTrack.objects.create(queue=queue, track=track, order=idx)
        return Response({'status': 'playlist added to queue'})

    @action(detail=False, methods=['post'], url_path='add-album/(?P<album_id>\\d+)')
    def add_album(self, request, album_id=None):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        album = Album.objects.get(pk=album_id)
        current_order = queue.queuetrack_set.count()
        for idx, track in enumerate(album.tracks.all()):
            QueueTrack.objects.create(queue=queue, track=track, order=current_order + idx)
        return Response({'status': 'album added to queue'})

    @action(detail=False, methods=['post'], url_path='clear')
    def clear(self, request):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        queue.queuetrack_set.all().delete()
        return Response({'status': 'queue cleared'})

    @action(detail=False, methods=['get'], url_path='current-track')
    def current_track(self, request):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        queue_tracks = list(queue.queuetrack_set.order_by('order'))
        if not queue_tracks:
            return Response({'error': 'Queue is empty'}, status=status.HTTP_404_NOT_FOUND)
        # Lấy track ở vị trí current_index
        idx = min(queue.current_index, len(queue_tracks) - 1)
        current_qt = queue_tracks[idx]
        serializer = QueueTrackSerializer(current_qt)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='set-current/(?P<track_id>\\d+)')
    def set_current(self, request, track_id=None):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        track = Track.objects.get(pk=track_id)
        # Lấy tất cả QueueTrack theo thứ tự
        queue_tracks = list(queue.queuetrack_set.order_by('order'))
        # Kiểm tra track đã có trong queue chưa
        track_ids = [qt.track.id for qt in queue_tracks]
        if track.id not in track_ids:
            # Thêm vào cuối queue
            order = len(queue_tracks)
            qt = QueueTrack.objects.create(queue=queue, track=track, order=order)
            queue_tracks.append(qt)
            track_ids.append(track.id)
        # Cập nhật current_index trỏ đến vị trí track này
        current_idx = track_ids.index(track.id)
        queue.current_index = current_idx
        queue.save(update_fields=['current_index'])
        return Response({'status': 'current track set', 'current_index': current_idx}) 