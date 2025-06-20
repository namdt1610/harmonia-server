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
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from tracks.serializers import TrackSerializer
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
import json
from django.utils import timezone
from django.db import models
import redis
from django.conf import settings
import logging

# Add Redis lock for distributed synchronization
redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)

# Configure logger
logger = logging.getLogger(__name__)

class QueueViewSet(viewsets.ModelViewSet):
    """
    RESTful Queue management ViewSet.
    Provides comprehensive queue management functionality for music playback.
    """
    swagger_tags = ['Queues']
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated, HasCustomPermission]
    CACHE_TIMEOUT = 300  # 5 minutes
    MAX_QUEUES_PER_USER = 5
    LOCK_TIMEOUT = 10  # 10 seconds for redis lock

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

    def _get_cache_key(self, user_id):
        return f"queue_{user_id}"

    def _get_lock_key(self, user_id):
        return f"queue_lock_{user_id}"

    def _get_queue_from_cache(self, user_id):
        cache_key = self._get_cache_key(user_id)
        return cache.get(cache_key)

    def _set_queue_in_cache(self, user_id, queue_data):
        cache_key = self._get_cache_key(user_id)
        cache.set(cache_key, queue_data, self.CACHE_TIMEOUT)

    def _invalidate_cache(self, user_id):
        """Invalidate cache when data changes"""
        cache_key = self._get_cache_key(user_id)
        cache.delete(cache_key)

    def _with_queue_lock(self, user_id, func, *args, **kwargs):
        """Execute function with distributed lock to prevent race conditions"""
        lock_key = self._get_lock_key(user_id)
        lock = redis_client.lock(lock_key, timeout=self.LOCK_TIMEOUT)
        
        try:
            if lock.acquire(blocking=True, blocking_timeout=5):
                # Invalidate cache before operation to ensure fresh data
                self._invalidate_cache(user_id)
                result = func(*args, **kwargs)
                return result
            else:
                raise Exception("Could not acquire lock for queue operation")
        finally:
            try:
                lock.release()
            except:
                pass  # Lock may have expired

    def _cleanup_queues(self, user):
        """Clean up duplicate queues for a user, keeping only the most recent ones"""
        with transaction.atomic():
            queues = Queue.objects.filter(user=user).order_by('-id')
            if queues.count() > self.MAX_QUEUES_PER_USER:
                # Keep the most recent queues
                latest_queues = queues[:self.MAX_QUEUES_PER_USER]
                Queue.objects.filter(user=user).exclude(id__in=latest_queues.values_list('id', flat=True)).update(
                    is_deleted=True,
                    deleted_at=timezone.now()
                )
                return latest_queues.first()
            return queues.first()

    def _send_queue_update(self, user, force_sync=False, auto_play=False):
        """Send queue update through WebSocket with improved error handling"""
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                logger.error("Channel layer not available for WebSocket updates")
                return

            queue = Queue.objects.filter(user=user).first()
            if not queue:
                # Send empty queue update
                queue_data = {
                    'tracks': [], 
                    'current_index': 0,
                    'timestamp': timezone.now().isoformat()
                }
                message = {
                    "type": "queue_update",
                    "queue": queue_data,
                }
                if force_sync:
                    message["action"] = "sync_required"
                if auto_play:
                    message["auto_play"] = True
                    
                async_to_sync(channel_layer.group_send)(
                    f"queue_{user.id}",
                    message
                )
                return

            # Get queue data with optimized query
            queue_tracks = QueueTrack.objects.filter(
                queue=queue,
                is_deleted=False
            ).select_related(
                'track',
                'track__artist',
                'track__album'
            ).order_by('order')

            # Prepare tracks data
            tracks = []
            for qt in queue_tracks:
                try:
                    track_data = TrackSerializer(qt.track).data
                    tracks.append({
                        'id': qt.id,
                        'track': track_data,
                        'order': qt.order
                    })
                except Exception as e:
                    logger.error(f"Error serializing track {qt.track.id}: {e}")
                    continue

            # Prepare queue data
            queue_data = {
                'tracks': tracks,
                'current_index': queue.current_index,
                'timestamp': timezone.now().isoformat(),
                'total_tracks': len(tracks)
            }

            # Update cache
            self._set_queue_in_cache(user.id, queue_data)

            # Send update through WebSocket
            message = {
                "type": "queue_update",
                "queue": queue_data,
            }
            
            if force_sync:
                message["action"] = "sync_required"
            if auto_play:
                message["auto_play"] = True
                logger.info(f"Sending auto-play signal for user {user.id}")

            async_to_sync(channel_layer.group_send)(
                f"queue_{user.id}",
                message
            )

            logger.info(f"Queue update sent for user {user.id} with {len(tracks)} tracks (auto_play: {auto_play})")

        except Exception as e:
            logger.error(f"Error sending queue update for user {user.id}: {e}")
            # Invalidate cache on error to force fresh data next time
            self._invalidate_cache(user.id)

    @transaction.atomic
    def perform_create(self, serializer):
        def _create():
            serializer.save(user=self.request.user)
            self._send_queue_update(self.request.user, force_sync=True)
        
        self._with_queue_lock(self.request.user.id, _create)

    @transaction.atomic
    def perform_update(self, serializer):
        def _update():
            serializer.save()
            self._send_queue_update(self.request.user, force_sync=True)
        
        self._with_queue_lock(self.request.user.id, _update)

    @transaction.atomic
    def perform_destroy(self, instance):
        def _destroy():
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
            instance.save()
            self._send_queue_update(self.request.user, force_sync=True)
        
        self._with_queue_lock(self.request.user.id, _destroy)

    @swagger_auto_schema(
        tags=['Queues'],
        operation_description="Get the current user's queue with tracks",
        responses={
            200: openapi.Response(
                description="Current user's queue with tracks",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'tracks': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        ),
                        'current_index': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        # Return the current user's queue instead of all queues
        queue = self._cleanup_queues(request.user)
        if not queue:
            queue, _ = Queue.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(queue)
        return Response(serializer.data)

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
        def _add_track():
            try:
                with transaction.atomic():
                    queue, _ = Queue.objects.get_or_create(user=request.user)
                    track = Track.objects.select_related('artist', 'album').get(pk=track_id)
                    
                    # Check if track already exists in active queue
                    existing_active_track = QueueTrack.objects.filter(
                        queue=queue,
                        track=track,
                        is_deleted=False
                    ).first()
                    
                    if existing_active_track:
                        return Response({
                            'status': 'track already in queue',
                            'queue_track_id': existing_active_track.id
                        })
                    
                    # Check if there's a soft-deleted version of this track
                    existing_deleted_track = QueueTrack.objects.filter(
                        queue=queue,
                        track=track,
                        is_deleted=True
                    ).first()

                    if existing_deleted_track:
                        # Reactivate the soft-deleted track
                        max_order = QueueTrack.objects.filter(
                            queue=queue,
                            is_deleted=False
                        ).aggregate(max_order=models.Max('order'))['max_order'] or 0

                        existing_deleted_track.is_deleted = False
                        existing_deleted_track.deleted_at = None
                        existing_deleted_track.order = max_order + 1
                        existing_deleted_track.save()
                        
                        queue_track = existing_deleted_track
                    else:
                        # Get current max order for new track
                        max_order = QueueTrack.objects.filter(
                            queue=queue,
                            is_deleted=False
                        ).aggregate(max_order=models.Max('order'))['max_order'] or 0

                        # Create new queue track
                        queue_track = QueueTrack.objects.create(
                            queue=queue,
                            track=track,
                            order=max_order + 1
                        )

                    self._send_queue_update(request.user)
                    return Response({
                        'status': 'track added to queue',
                        'queue_track_id': queue_track.id
                    })
            except Track.DoesNotExist:
                return Response(
                    {'error': 'Track not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"Error adding track to queue: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        try:
            return self._with_queue_lock(request.user.id, _add_track)
        except Exception as e:
            return Response(
                {'error': 'Failed to acquire queue lock'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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
        def _remove_track():
            try:
                with transaction.atomic():
                    queue, _ = Queue.objects.get_or_create(user=request.user)
                    queue_track = QueueTrack.objects.get(
                        queue=queue,
                        track_id=track_id,
                        is_deleted=False
                    )
                    
                    # Soft delete the track
                    queue_track.is_deleted = True
                    queue_track.deleted_at = timezone.now()
                    queue_track.save()

                    # Reorder remaining tracks
                    QueueTrack.objects.filter(
                        queue=queue,
                        order__gt=queue_track.order,
                        is_deleted=False
                    ).update(order=F('order') - 1)

                    # Adjust current_index if needed
                    if queue.current_index >= queue_track.order:
                        remaining_tracks = QueueTrack.objects.filter(
                            queue=queue,
                            is_deleted=False
                        ).count()
                        
                        if remaining_tracks == 0:
                            queue.current_index = 0
                        elif queue.current_index > 0:
                            queue.current_index -= 1
                        
                        queue.save(update_fields=['current_index'])

                    self._send_queue_update(request.user)
                    return Response({'status': 'track removed from queue'})
            except QueueTrack.DoesNotExist:
                return Response(
                    {'error': 'Track not found in queue'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"Error removing track from queue: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        try:
            return self._with_queue_lock(request.user.id, _remove_track)
        except Exception as e:
            return Response(
                {'error': 'Failed to acquire queue lock'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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
        try:
            with transaction.atomic():
                # Get or create queue for user
                queue, created = Queue.objects.get_or_create(user=request.user)
                
                if not created:
                    # Soft delete existing queue tracks
                    QueueTrack.objects.filter(
                        queue=queue,
                        is_deleted=False
                    ).update(
                        is_deleted=True,
                        deleted_at=timezone.now()
                    )

                playlist = Playlist.objects.select_related('user').get(pk=playlist_id)

                # Add tracks with optimized query
                tracks = playlist.tracks.select_related('artist', 'album').all()
                
                # Create new queue tracks, handling existing ones properly
                queue_tracks_to_create = []
                for idx, track in enumerate(tracks):
                    # Check if this track already exists in this queue
                    existing_qt = QueueTrack.objects.filter(
                        queue=queue, 
                        track=track
                    ).first()
                    
                    if existing_qt:
                        # Reactivate existing track
                        existing_qt.is_deleted = False
                        existing_qt.deleted_at = None
                        existing_qt.order = idx
                        existing_qt.save()
                    else:
                        # Add to bulk create list
                        queue_tracks_to_create.append(
                            QueueTrack(queue=queue, track=track, order=idx)
                        )
                
                # Bulk create only new tracks
                if queue_tracks_to_create:
                    QueueTrack.objects.bulk_create(queue_tracks_to_create)

                # Reset current index
                queue.current_index = 0
                queue.save(update_fields=['current_index'])

                self._send_queue_update(request.user)
                return Response({'status': 'playlist added to queue'})
        except Playlist.DoesNotExist:
            return Response(
                {'error': 'Playlist not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        try:
            with transaction.atomic():
                queue, _ = Queue.objects.get_or_create(user=request.user)
                album = Album.objects.select_related('artist').get(pk=album_id)

                # Get current max order
                max_order = QueueTrack.objects.filter(
                    queue=queue,
                    is_deleted=False
                ).aggregate(max_order=models.Max('order'))['max_order'] or 0

                # Add tracks with optimized query
                tracks = album.tracks.select_related('artist', 'album').all()
                QueueTrack.objects.bulk_create([
                    QueueTrack(queue=queue, track=track, order=max_order + idx + 1)
                    for idx, track in enumerate(tracks)
                ])

                self._send_queue_update(request.user)
                return Response({'status': 'album added to queue'})
        except Album.DoesNotExist:
            return Response(
                {'error': 'Album not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        def _clear_queue():
            try:
                with transaction.atomic():
                    queue, _ = Queue.objects.get_or_create(user=request.user)
                    
                    # Log before clearing
                    tracks_count = QueueTrack.objects.filter(
                        queue=queue,
                        is_deleted=False
                    ).count()
                    logger.info(f"Clearing queue for user {request.user.id} with {tracks_count} tracks")
                    
                    # Soft delete all tracks
                    QueueTrack.objects.filter(
                        queue=queue,
                        is_deleted=False
                    ).update(
                        is_deleted=True,
                        deleted_at=timezone.now()
                    )

                    # Reset current index
                    queue.current_index = 0
                    queue.save(update_fields=['current_index'])

                    # Force invalidate cache before sending update
                    self._invalidate_cache(request.user.id)
                    
                    # Send WebSocket update with force sync
                    self._send_queue_update(request.user, force_sync=True)
                    
                    logger.info(f"Queue cleared successfully for user {request.user.id}")
                    return Response({'status': 'queue cleared'})
            except Exception as e:
                logger.error(f"Error clearing queue: {e}")
                # Clean up cache on error
                self._invalidate_cache(request.user.id)
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        try:
            return self._with_queue_lock(request.user.id, _clear_queue)
        except Exception as e:
            logger.error(f"Failed to acquire queue lock for clear operation: {e}")
            return Response(
                {'error': 'Failed to acquire queue lock'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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
        try:
            queue, _ = Queue.objects.get_or_create(user=request.user)
            queue_tracks = list(QueueTrack.objects.filter(
                queue=queue,
                is_deleted=False
            ).select_related(
                'track',
                'track__artist',
                'track__album'
            ).order_by('order'))

            if not queue_tracks:
                return Response(
                    {'error': 'Queue is empty'},
                    status=status.HTTP_404_NOT_FOUND
                )

            idx = min(queue.current_index, len(queue_tracks) - 1)
            current_qt = queue_tracks[idx]
            serializer = QueueTrackSerializer(current_qt)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        def _set_current():
            try:
                with transaction.atomic():
                    queue, _ = Queue.objects.get_or_create(user=request.user)
                    track = Track.objects.select_related('artist', 'album').get(pk=track_id)

                    # Get all active queue tracks ordered by their position
                    queue_tracks = list(QueueTrack.objects.filter(
                        queue=queue,
                        is_deleted=False
                    ).select_related(
                        'track',
                        'track__artist',
                        'track__album'
                    ).order_by('order'))

                    # Find the target track in the queue
                    target_index = None
                    for i, qt in enumerate(queue_tracks):
                        if qt.track.id == int(track_id):
                            target_index = i
                            break

                    if target_index is not None:
                        # Track is already in queue, just update current_index
                        queue.current_index = target_index
                        queue.save(update_fields=['current_index'])
                        
                        logger.info(f"Set current track to index {target_index} for user {request.user.id}")
                        
                        # Send queue update with play indication
                        self._send_queue_update(request.user, force_sync=True, auto_play=True)
                        
                        return Response({
                            'status': 'current track set',
                            'current_index': target_index,
                            'track': {
                                'id': track.id,
                                'title': track.title,
                                'artist': track.artist.name if track.artist else None
                            },
                            'auto_play': True  # Signal frontend to start playing
                        })
                    else:
                        # Track not in queue, add it and set as current
                        # Check if there's a soft-deleted version first
                        existing_deleted_track = QueueTrack.objects.filter(
                            queue=queue,
                            track=track,
                            is_deleted=True
                        ).first()

                        if existing_deleted_track:
                            # Reactivate the soft-deleted track at the end
                            existing_deleted_track.is_deleted = False
                            existing_deleted_track.deleted_at = None
                            existing_deleted_track.order = len(queue_tracks)
                            existing_deleted_track.save()
                            new_index = len(queue_tracks)
                        else:
                            # Create new queue track at the end
                            QueueTrack.objects.create(
                                queue=queue, 
                                track=track, 
                                order=len(queue_tracks)
                            )
                            new_index = len(queue_tracks)

                        # Update current_index to the new track
                        queue.current_index = new_index
                        queue.save(update_fields=['current_index'])

                        logger.info(f"Added new track and set as current at index {new_index} for user {request.user.id}")
                        
                        # Send queue update with play indication
                        self._send_queue_update(request.user, force_sync=True, auto_play=True)
                        
                        return Response({
                            'status': 'track added and set as current',
                            'current_index': new_index,
                            'track': {
                                'id': track.id,
                                'title': track.title,
                                'artist': track.artist.name if track.artist else None
                            },
                            'auto_play': True  # Signal frontend to start playing
                        })
                        
            except Track.DoesNotExist:
                return Response(
                    {'error': 'Track not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"Error setting current track: {e}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        try:
            return self._with_queue_lock(request.user.id, _set_current)
        except Exception as e:
            logger.error(f"Failed to acquire queue lock for set_current operation: {e}")
            return Response(
                {'error': 'Failed to acquire queue lock'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

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