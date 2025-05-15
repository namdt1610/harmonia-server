from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from .models import Favorite
from .serializers import FavoriteSerializer
from music.serializers import TrackSerializer, AlbumSerializer, PlaylistSerializer, ArtistSerializer
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist
import logging

logger = logging.getLogger(__name__)

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
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
    
    @action(detail=True, methods=['post'], url_path='tracks/(?P<track_id>[^/.]+)')
    def add_track(self, request, track_id=None):
        if not track_id:
            return Response({'error': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if Favorite.objects.filter(user=request.user, track_id=track_id).exists():
            return Response({'error': 'Track already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
            
        Favorite.objects.create(user=request.user, track_id=track_id)
        return Response(status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='albums/(?P<album_id>[^/.]+)')
    def add_album(self, request, album_id=None):
        if not album_id:
            return Response({'error': 'album_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if Favorite.objects.filter(user=request.user, album_id=album_id).exists():
            return Response({'error': 'Album already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
            
        Favorite.objects.create(user=request.user, album_id=album_id)
        return Response(status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='playlists/(?P<playlist_id>[^/.]+)')
    def add_playlist(self, request, playlist_id=None):
        try:
            if not playlist_id:
                return Response({'error': 'playlist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            if Favorite.objects.filter(user=request.user, playlist_id=playlist_id).exists():
                return Response({'error': 'Playlist already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
            
            Favorite.objects.create(user=request.user, playlist_id=playlist_id)
            return Response(status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error adding playlist to favorites: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='artists/(?P<artist_id>[^/.]+)')
    def add_artist(self, request, artist_id=None):
        if not artist_id:
            return Response({'error': 'artist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if Favorite.objects.filter(user=request.user, artist_id=artist_id).exists():
            return Response({'error': 'Artist already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
            
        Favorite.objects.create(user=request.user, artist_id=artist_id)
        return Response(status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='tracks/(?P<track_id>[^/.]+)')
    def remove_track(self, request, track_id=None):
        if not track_id:
            return Response({'error': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        Favorite.objects.filter(user=request.user, track_id=track_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['delete'], url_path='albums/(?P<album_id>[^/.]+)')
    def remove_album(self, request, album_id=None):
        if not album_id:
            return Response({'error': 'album_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        Favorite.objects.filter(user=request.user, album_id=album_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['delete'], url_path='playlists/(?P<playlist_id>[^/.]+)')
    def remove_playlist(self, request, playlist_id=None):
        try:
            if not playlist_id:
                return Response({'error': 'playlist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            Favorite.objects.filter(user=request.user, playlist_id=playlist_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
                logger.error(f"Error removing playlist from favorites: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['delete'], url_path='artists/(?P<artist_id>[^/.]+)')
    def remove_artist(self, request, artist_id=None):
        if not artist_id:
            return Response({'error': 'artist_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        Favorite.objects.filter(user=request.user, artist_id=artist_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT) 