from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from .models import Favorite
from .serializers import FavoriteSerializer
from tracks.serializers import TrackSerializer
from albums.serializers import AlbumSerializer
from playlists.serializers import PlaylistSerializer
from artists.serializers import ArtistSerializer
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission

logger = logging.getLogger(__name__)

class FavoriteViewSet(viewsets.ModelViewSet):
    """
    RESTful Favorite management ViewSet.
    Provides comprehensive favorite management functionality for tracks, albums, artists, and playlists.
    """
    swagger_tags = ['Favorites']
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, HasCustomPermission]

    @property
    def required_permission(self):
        mapping = {
            'create': 'add_favorite',
            'update': 'edit_favorite',
            'partial_update': 'edit_favorite',
            'destroy': 'delete_favorite',
            'list': 'view_favorite',
            'retrieve': 'view_favorite'
        }
        return mapping.get(self.action)

    def get_queryset(self):
        queryset = Favorite.objects.filter(user=self.request.user)
        content_type = self.request.query_params.get('type', None)
        
        if content_type:
            queryset = queryset.filter(content_type=content_type)
            
        try:
            return queryset.select_related('track', 'artist', 'album', 'playlist')
        except Exception as e:
            logger.error(f"Error getting favorites: {str(e)}")
            # If playlist table doesn't exist, return queryset without related
            return queryset.select_related('track', 'artist', 'album')

    def perform_create(self, serializer):
        favorite = serializer.save(user=self.request.user)
        # Invalidate user's favorites cache
        cache.delete(f'favorites_{self.request.user.id}')

    def perform_destroy(self, instance):
        instance.delete()
        # Invalidate user's favorites cache
        cache.delete(f'favorites_{self.request.user.id}')

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Get a list of all favorites",
        responses={
            200: FavoriteSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Create a new favorite",
        request_body=FavoriteSerializer,
        responses={
            201: FavoriteSerializer,
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Get a specific favorite by ID",
        responses={
            200: FavoriteSerializer,
            404: "Not Found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Delete a favorite",
        responses={
            204: "No Content",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Partially update a favorite",
        request_body=FavoriteSerializer,
        responses={
            200: FavoriteSerializer,
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Get user's favorite tracks",
        responses={
            200: TrackSerializer(many=True),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def tracks(self, request):
        """Get user's favorite tracks"""
        cache_key = f'favorite_tracks_{request.user.id}'
        cached_tracks = cache.get(cache_key)
        
        if cached_tracks is None:
            tracks = Track.objects.filter(favorites__user=request.user)
            cached_tracks = TrackSerializer(tracks, many=True).data
            cache.set(cache_key, cached_tracks, 300)  # 5 minutes cache
            
        return Response(cached_tracks)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Get user's favorite artists",
        responses={
            200: ArtistSerializer(many=True),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def artists(self, request):
        """Get user's favorite artists"""
        cache_key = f'favorite_artists_{request.user.id}'
        cached_artists = cache.get(cache_key)
        
        if cached_artists is None:
            artists = Artist.objects.filter(favorites__user=request.user)
            cached_artists = ArtistSerializer(artists, many=True).data
            cache.set(cache_key, cached_artists, 300)  # 5 minutes cache
            
        return Response(cached_artists)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Get user's favorite albums",
        responses={
            200: AlbumSerializer(many=True),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def albums(self, request):
        """Get user's favorite albums"""
        cache_key = f'favorite_albums_{request.user.id}'
        cached_albums = cache.get(cache_key)
        
        if cached_albums is None:
            albums = Album.objects.filter(favorites__user=request.user)
            cached_albums = AlbumSerializer(albums, many=True).data
            cache.set(cache_key, cached_albums, 300)  # 5 minutes cache
            
        return Response(cached_albums)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Get user's favorite playlists",
        responses={
            200: PlaylistSerializer(many=True),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def playlists(self, request):
        """Get user's favorite playlists"""
        try:
            cache_key = f'favorite_playlists_{request.user.id}'
            cached_playlists = cache.get(cache_key)
        
            if cached_playlists is None:
                playlists = Playlist.objects.filter(favorites__user=request.user)
                cached_playlists = PlaylistSerializer(playlists, many=True).data
                cache.set(cache_key, cached_playlists, 300)  # 5 minutes cache
            
            return Response(cached_playlists)
        
        except Exception as e:
            logger.error(f"Error getting favorite playlists: {str(e)}")
            return Response([], status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Add a track to favorites",
        responses={
            201: "Track added to favorites",
            400: "Bad Request - track_id is required or track already in favorites",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['post'], url_path='tracks/(?P<track_id>[^/.]+)')
    def add_track(self, request, track_id=None):
        if not track_id:
            return Response({'error': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if Favorite.objects.filter(user=request.user, track_id=track_id).exists():
            return Response({'error': 'Track already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=request.user, track_id=track_id, content_type='track')
        return Response(status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Add an album to favorites",
        responses={
            201: "Album added to favorites",
            400: "Bad Request - album_id is required or album already in favorites",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['post'], url_path='albums/(?P<album_id>[^/.]+)')
    def add_album(self, request, album_id=None):
        if not album_id:
            return Response({'error': 'album_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if Favorite.objects.filter(user=request.user, album_id=album_id).exists():
            return Response({'error': 'Album already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=request.user, album_id=album_id, content_type='album')
        return Response(status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Add a playlist to favorites",
        responses={
            201: "Playlist added to favorites",
            400: "Bad Request - playlist_id is required or playlist already in favorites",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['post'], url_path='playlists/(?P<playlist_id>[^/.]+)')
    def add_playlist(self, request, playlist_id=None):
        if not playlist_id:
            return Response({'error': 'playlist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if Favorite.objects.filter(user=request.user, playlist_id=playlist_id).exists():
            return Response({'error': 'Playlist already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=request.user, playlist_id=playlist_id, content_type='playlist')
        return Response(status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Add an artist to favorites",
        responses={
            201: "Artist added to favorites",
            400: "Bad Request - artist_id is required or artist already in favorites",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['post'], url_path='artists/(?P<artist_id>[^/.]+)')
    def add_artist(self, request, artist_id=None):
        if not artist_id:
            return Response({'error': 'artist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if Favorite.objects.filter(user=request.user, artist_id=artist_id).exists():
            return Response({'error': 'Artist already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.create(user=request.user, artist_id=artist_id, content_type='artist')
        return Response(status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Remove a track from favorites",
        responses={
            204: "Track removed from favorites",
            400: "Bad Request - track_id is required",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['delete'], url_path='tracks/(?P<track_id>[^/.]+)')
    def remove_track(self, request, track_id=None):
        if not track_id:
            return Response({'error': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.filter(user=request.user, track_id=track_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Remove an album from favorites",
        responses={
            204: "Album removed from favorites",
            400: "Bad Request - album_id is required",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['delete'], url_path='albums/(?P<album_id>[^/.]+)')
    def remove_album(self, request, album_id=None):
        if not album_id:
            return Response({'error': 'album_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.filter(user=request.user, album_id=album_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Remove a playlist from favorites",
        responses={
            204: "Playlist removed from favorites",
            400: "Bad Request - playlist_id is required",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['delete'], url_path='playlists/(?P<playlist_id>[^/.]+)')
    def remove_playlist(self, request, playlist_id=None):
        if not playlist_id:
            return Response({'error': 'playlist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.filter(user=request.user, playlist_id=playlist_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        tags=['Favorites'],
        operation_description="Remove an artist from favorites",
        responses={
            204: "Artist removed from favorites",
            400: "Bad Request - artist_id is required",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['delete'], url_path='artists/(?P<artist_id>[^/.]+)')
    def remove_artist(self, request, artist_id=None):
        if not artist_id:
            return Response({'error': 'artist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        Favorite.objects.filter(user=request.user, artist_id=artist_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 