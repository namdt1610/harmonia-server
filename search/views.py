from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.core.cache import cache
from .models import SearchHistory
from .serializers import SearchHistorySerializer
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist
from tracks.serializers import TrackSerializer
from artists.serializers import ArtistSerializer
from albums.serializers import AlbumSerializer
from playlists.serializers import PlaylistSerializer
import logging

logger = logging.getLogger(__name__)

class SearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def global_search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Missing search query"}, status=status.HTTP_400_BAD_REQUEST)

        # Cache key for search results
        cache_key = f'search_results_{query}'
        cached_results = cache.get(cache_key)
        
        if cached_results is None:
            # Search in different models
            tracks = Track.objects.filter(
                Q(title__icontains=query) |
                Q(artist__name__icontains=query) |
                Q(album__title__icontains=query)
            )[:10]
            
            artists = Artist.objects.filter(
                Q(name__icontains=query) |
                Q(bio__icontains=query)
            )[:10]
            
            albums = Album.objects.filter(
                Q(title__icontains=query) |
                Q(artist__name__icontains=query) |
                Q(description__icontains=query)
            )[:10]
            
            # Try to get playlists, catch exception if table doesn't exist
            try:
                playlists = Playlist.objects.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query)
                ).filter(is_public=True)[:10]
                playlist_data = PlaylistSerializer(playlists, many=True).data
            except Exception as e:
                logger.error(f"Error getting playlists in search: {str(e)}")
                playlist_data = []

            # Prepare results
            cached_results = {
                "tracks": TrackSerializer(tracks, many=True).data,
                "artists": ArtistSerializer(artists, many=True).data,
                "albums": AlbumSerializer(albums, many=True).data,
                "playlists": playlist_data
            }
            
            # Cache results for 5 minutes
            cache.set(cache_key, cached_results, 300)

        # Record search history for authenticated users
        if request.user.is_authenticated:
            total_results = (
                len(cached_results['tracks']) +
                len(cached_results['artists']) +
                len(cached_results['albums']) +
                len(cached_results['playlists'])
            )
            SearchHistory.objects.create(
                user=request.user,
                query=query,
                result_count=total_results
            )

        return Response(cached_results)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user's search history"""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        history = SearchHistory.objects.filter(user=request.user)[:20]
        serializer = SearchHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Get search suggestions based on popular searches"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Missing search query"}, status=status.HTTP_400_BAD_REQUEST)

        # Get popular searches that start with the query
        suggestions = SearchHistory.objects.filter(
            query__istartswith=query
        ).values('query').annotate(
            count=models.Count('id')
        ).order_by('-count')[:5]

        return Response([s['query'] for s in suggestions]) 