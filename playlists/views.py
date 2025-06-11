from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db.models import Count
from django.db.models import Q
from .serializers import PlaylistSerializer
from .models import Playlist
from tracks.models import Track
from user_activity.models import UserActivity
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission

class PlaylistViewSet(viewsets.ModelViewSet):
    """
    RESTful Playlist management ViewSet.
    Provides comprehensive playlist management functionality including creating, updating,
    and managing tracks within playlists.
    """
    swagger_tags = ['Playlists']
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated, HasCustomPermission]
    
    @property
    def required_permission(self):
        mapping = {
            'create': 'add_playlist',
            'update': 'edit_playlist',
            'partial_update': 'edit_playlist',
            'destroy': 'delete_playlist',
            'list': 'view_playlist',
            'retrieve': 'view_playlist'
        }
        return mapping.get(self.action)
    
    def get_queryset(self):
        queryset = Playlist.objects.select_related('user').prefetch_related('tracks')
        
        if self.action == 'list':
            # Cache the queryset for 5 minutes
            cache_key = f'playlist_list_{self.request.user.id}'
            cached_queryset = cache.get(cache_key)
            if cached_queryset is None:
                cached_queryset = list(queryset.filter(user=self.request.user))
                cache.set(cache_key, cached_queryset, 300)  # 5 minutes cache
            return cached_queryset
            
        return queryset.filter(Q(is_public=True) | Q(user=self.request.user))

    def perform_create(self, serializer):
        playlist = serializer.save(user=self.request.user)
        # Invalidate user's playlist cache
        cache.delete(f'playlist_list_{self.request.user.id}')
        # Record create playlist activity
        UserActivity.objects.create(
            user=self.request.user,
            playlist=playlist,
            action='create_playlist'
        )

    def perform_update(self, serializer):
        serializer.save()
        # Invalidate user's playlist cache
        cache.delete(f'playlist_list_{self.request.user.id}')

    def perform_destroy(self, instance):
        # Record user activity before deletion
        UserActivity.objects.create(
            user=self.request.user,
            playlist=instance,
            action='delete_playlist'
        )
        instance.delete()
        # Invalidate user's playlist cache
        cache.delete(f'playlist_list_{self.request.user.id}')

    @swagger_auto_schema(
        tags=['Playlists'],
        operation_description="Get featured playlists (playlists with most tracks)",
        responses={
            200: PlaylistSerializer(many=True)
        }
    )
    @action(detail=False)
    def featured(self, request):
        """Get featured playlists"""
        cache_key = 'featured_playlists'
        cached_playlists = cache.get(cache_key)
        
        if cached_playlists is None:
            # Get playlists with most tracks
            playlists = Playlist.objects.annotate(
                track_count=Count('tracks')
            ).order_by('-track_count')[:10]
            cached_playlists = self.get_serializer(playlists, many=True).data
            cache.set(cache_key, cached_playlists, 1800)  # 30 minutes cache
            
        return Response(cached_playlists)

    @swagger_auto_schema(
        tags=['Playlists'],
        operation_description="Add a track to a playlist",
        responses={
            200: "Track added successfully",
            404: "Playlist or Track not found"
        }
    )
    @action(detail=True, methods=['post'],url_path='add-track/(?P<track_id>[^/.]+)')
    def add_track(self, request, pk=None, track_id=None):
        try:
            playlist = self.get_object()
            track = Track.objects.get(id=track_id)
            
            playlist.tracks.add(track)
            # Create activity record
            UserActivity.objects.create(
                user=self.request.user,
                playlist=playlist,
                track=track,
                action='add_to_playlist'
            )
            
            return Response({'status': 'track added'}, status=status.HTTP_200_OK)
        except Playlist.DoesNotExist:
            return Response({'error': 'Playlist not found'}, status=status.HTTP_404_NOT_FOUND)
        except Track.DoesNotExist:
            return Response({'error': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=['Playlists'],
        operation_description="Remove a track from a playlist",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['track_id'],
            properties={
                'track_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID of the track to remove')
            }
        ),
        responses={
            200: "Track removed successfully",
            400: "Bad Request - track_id is required or invalid"
        }
    )
    @action(detail=True, methods=['post'])
    def remove_track(self, request, pk=None):
        playlist = self.get_object()
        track_id = request.data.get('track_id')
        
        if not track_id:
            return Response({'error': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            playlist.tracks.remove(track_id)
            cache.delete(f'playlist_list_{self.request.user.id}')
            return Response({'status': 'track removed'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=['Playlists'],
        operation_description="Get all public playlists, optionally filtered by user",
        responses={
            200: PlaylistSerializer(many=True)
        }
    )
    @action(detail=False, methods=['get'], url_path='public')
    def public(self, request):
        """
        Return all public playlists, optionally filter by user.
        """
        user = request.query_params.get('user')
        qs = Playlist.objects.filter(is_public=True)
        if user:
            qs = qs.filter(user__username=user)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['Playlists'],
        operation_description="Get a list of all playlists",
        responses={
            200: openapi.Response(
                description="List of playlists",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                        }
                    )
                )
            ),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Playlists'],
        operation_description="Create a new playlist",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        ),
        responses={
            201: openapi.Response(
                description="Playlist created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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
        tags=['Playlists'],
        operation_description="Get a specific playlist by ID",
        responses={
            200: openapi.Response(
                description="Playlist details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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
        tags=['Playlists'],
        operation_description="Update a playlist",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        ),
        responses={
            200: openapi.Response(
                description="Playlist updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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
        tags=['Playlists'],
        operation_description="Delete a playlist",
        responses={
            204: "No Content",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Playlists'],
        operation_description="Partially update a playlist",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN)
            }
        ),
        responses={
            200: openapi.Response(
                description="Playlist partially updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN),
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