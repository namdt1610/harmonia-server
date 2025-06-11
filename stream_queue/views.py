from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Queue, QueueTrack
from .serializers import QueueSerializer, QueueTrackSerializer
from tracks.models import Track
from playlists.models import Playlist
from albums.models import Album
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission

class QueueViewSet(viewsets.ModelViewSet):
    """
    RESTful Queue management ViewSet.
    Provides comprehensive queue management functionality for music playback.
    """
    swagger_tags = ['Queues']
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated, HasCustomPermission]

    @property
    def required_permission(self):
        mapping = {
            'create': 'add_queue',
            'update': 'edit_queue',
            'partial_update': 'edit_queue',
            'destroy': 'delete_queue',
            'list': 'view_queue',
            'retrieve': 'view_queue',
            'current_queue': 'view_queue'
        }
        return mapping.get(self.action)

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

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Get a list of all queues",
        responses={
            200: QueueSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Create a new queue",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'current_index': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            201: openapi.Response(
                description="Queue created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'current_index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Get a specific queue by ID",
        responses={
            200: openapi.Response(
                description="Queue details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'current_index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            404: "Not Found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Update a queue",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'current_index': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: openapi.Response(
                description="Queue updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'current_index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Delete a queue",
        responses={
            204: "No Content",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Get the current queue",
        responses={
            200: openapi.Response(
                description="Current queue details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'current_index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'], url_path='current-queue')
    def current_queue(self, request):
        # Clean up any duplicate queues first
        queue = self._cleanup_queues(request.user)
        if not queue:
            queue, _ = Queue.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(queue)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Add a track to the queue",
        responses={
            200: openapi.Response(
                description="Track added successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request - track_id is required",
            401: "Unauthorized",
            404: "Track not found"
        }
    )
    @action(detail=False, methods=['post'], url_path='add-track/(?P<track_id>\\d+)')
    def add_track(self, request, track_id=None):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        track = Track.objects.get(pk=track_id)
        order = queue.queuetrack_set.count()
        QueueTrack.objects.create(queue=queue, track=track, order=order)
        return Response({'status': 'track added to queue'})

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Remove a track from the queue",
        responses={
            200: openapi.Response(
                description="Track removed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request - track_id is required",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['post'], url_path='remove-track/(?P<track_id>\\d+)')
    def remove_track(self, request, track_id=None):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        QueueTrack.objects.filter(queue=queue, track_id=track_id).delete()
        return Response({'status': 'track removed from queue'})

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Add a playlist to the queue",
        responses={
            200: openapi.Response(
                description="Playlist added successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request - playlist_id is required",
            401: "Unauthorized",
            404: "Playlist not found"
        }
    )
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

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Add an album to the queue",
        responses={
            200: openapi.Response(
                description="Album added successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request - album_id is required",
            401: "Unauthorized",
            404: "Album not found"
        }
    )
    @action(detail=False, methods=['post'], url_path='add-album/(?P<album_id>\\d+)')
    def add_album(self, request, album_id=None):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        album = Album.objects.get(pk=album_id)
        current_order = queue.queuetrack_set.count()
        for idx, track in enumerate(album.tracks.all()):
            QueueTrack.objects.create(queue=queue, track=track, order=current_order + idx)
        return Response({'status': 'album added to queue'})

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Clear the queue",
        responses={
            200: openapi.Response(
                description="Queue cleared successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['post'], url_path='clear')
    def clear(self, request):
        queue, _ = Queue.objects.get_or_create(user=request.user)
        queue.queuetrack_set.all().delete()
        return Response({'status': 'queue cleared'})

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Get the current track in the queue",
        responses={
            200: openapi.Response(
                description="Current track details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'queue': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'track': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'order': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            401: "Unauthorized",
            404: "Queue is empty"
        }
    )
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

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Set the current track in the queue",
        responses={
            200: openapi.Response(
                description="Current track set successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'current_index': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            400: "Bad Request - track_id is required",
            401: "Unauthorized",
            404: "Track not found"
        }
    )
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

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Partially update a queue",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'current_index': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={
            200: openapi.Response(
                description="Queue partially updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'current_index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs) 