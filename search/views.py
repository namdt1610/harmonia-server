from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Value, CharField, Case, When, IntegerField
from django.core.cache import cache
from django.core.paginator import Paginator
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
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import re

logger = logging.getLogger(__name__)

class SearchViewSet(viewsets.ViewSet):
    swagger_tags = ['Search']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def _highlight_text(self, text, query):
        """Highlight matching text in search results"""
        if not text or not query:
            return text
        pattern = re.compile(f'({re.escape(query)})', re.IGNORECASE)
        return pattern.sub(r'<mark>\1</mark>', text)

    def _get_search_results(self, request, query, content_type=None, page=1, page_size=10):
        """Get search results with ranking and highlighting"""
        results = {
            "tracks": [],
            "artists": [],
            "albums": [],
            "playlists": []
        }

        if content_type in [None, 'tracks']:
            # For tracks, we search in title and related fields
            exact_match = Q(title__iexact=query)
            contains_match = Q(title__icontains=query)
            
            tracks = Track.objects.annotate(
                match_type=Case(
                    When(exact_match, then=Value(1)),
                    When(contains_match, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).filter(
                Q(title__icontains=query) |
                Q(artist__name__icontains=query) |
                Q(album__title__icontains=query)
            ).order_by('match_type', '-play_count')[:50]

            track_data = TrackSerializer(tracks, many=True, context={'request': request}).data
            for track in track_data:
                track['title'] = self._highlight_text(track['title'], query)
            results['tracks'] = track_data

        if content_type in [None, 'artists']:
            # For artists, we search in name and bio
            exact_match = Q(name__iexact=query)
            contains_match = Q(name__icontains=query)
            
            artists = Artist.objects.annotate(
                match_type=Case(
                    When(exact_match, then=Value(1)),
                    When(contains_match, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).filter(
                Q(name__icontains=query) |
                Q(bio__icontains=query)
            ).order_by('match_type', 'name')[:50]  # Order by match type and name

            artist_data = ArtistSerializer(artists, many=True, context={'request': request}).data
            for artist in artist_data:
                artist['name'] = self._highlight_text(artist['name'], query)
            results['artists'] = artist_data

        if content_type in [None, 'albums']:
            # For albums, we search in title and description
            exact_match = Q(title__iexact=query)
            contains_match = Q(title__icontains=query)
            
            albums = Album.objects.annotate(
                match_type=Case(
                    When(exact_match, then=Value(1)),
                    When(contains_match, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            ).filter(
                Q(title__icontains=query) |
                Q(artist__name__icontains=query) |
                Q(description__icontains=query)
            ).order_by('match_type', '-release_date')[:50]

            album_data = AlbumSerializer(albums, many=True, context={'request': request}).data
            for album in album_data:
                album['title'] = self._highlight_text(album['title'], query)
            results['albums'] = album_data

        if content_type in [None, 'playlists']:
            try:
                # For playlists, we search in name and description
                exact_match = Q(name__iexact=query)
                contains_match = Q(name__icontains=query)
                
                playlists = Playlist.objects.annotate(
                    match_type=Case(
                        When(exact_match, then=Value(1)),
                        When(contains_match, then=Value(2)),
                        default=Value(3),
                        output_field=IntegerField(),
                    )
                ).filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query)
                ).filter(is_public=True).order_by('match_type', '-created_at')[:50]

                playlist_data = PlaylistSerializer(playlists, many=True, context={'request': request}).data
                for playlist in playlist_data:
                    playlist['name'] = self._highlight_text(playlist['name'], query)
                results['playlists'] = playlist_data
            except Exception as e:
                logger.error(f"Error getting playlists in search: {str(e)}")
                results['playlists'] = []

        return results

    @swagger_auto_schema(
        tags=['Search'],
        operation_description="Perform a global search across tracks, artists, albums, and playlists",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query", type=openapi.TYPE_STRING),
            openapi.Parameter('type', openapi.IN_QUERY, description="Content type filter (tracks, artists, albums, playlists)", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Results per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response(
                description="Search results",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'tracks': TrackSerializer(many=True),
                        'artists': ArtistSerializer(many=True),
                        'albums': AlbumSerializer(many=True),
                        'playlists': PlaylistSerializer(many=True),
                        'total_results': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'page': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'total_pages': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            400: "Bad Request - Missing search query",
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def global_search(self, request):
        query = request.query_params.get('q', '')
        content_type = request.query_params.get('type')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        if not query:
            return Response({"error": "Missing search query"}, status=status.HTTP_400_BAD_REQUEST)

        # Cache key for search results
        cache_key = f'search_results_{query}_{content_type}_{page}_{page_size}'
        cached_results = cache.get(cache_key)
        
        if cached_results is None:
            # Get search results
            results = self._get_search_results(request, query, content_type, page, page_size)
            
            # Calculate total results
            total_results = sum(len(v) for v in results.values())
            
            # Prepare paginated response
            response_data = {
                **results,
                'total_results': total_results,
                'page': page,
                'total_pages': (total_results + page_size - 1) // page_size
            }
            
            # Cache results for 5 minutes
            cache.set(cache_key, response_data, 300)
            cached_results = response_data

        # Record search history for authenticated users
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            try:
                SearchHistory.objects.create(
                    user=user,
                    query=query,
                    result_count=cached_results['total_results']
                )
            except Exception as e:
                logger.error(f"Error recording search history: {str(e)}")

        return Response(cached_results)

    @swagger_auto_schema(
        tags=['Search'],
        operation_description="Get user's search history",
        responses={
            200: SearchHistorySerializer(many=True),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user's search history"""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        history = SearchHistory.objects.filter(user=user)[:20]
        serializer = SearchHistorySerializer(history, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['Search'],
        operation_description="Get search suggestions based on popular searches",
        responses={
            200: openapi.Response(
                description="List of search suggestions",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING)
                )
            ),
            400: "Bad Request - Missing search query"
        }
    )
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
            count=Count('id')
        ).order_by('-count')[:5]

        return Response([s['query'] for s in suggestions]) 