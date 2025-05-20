from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging
from django.db.models import Q

# Import models from separate apps
from artists.models import Artist
from tracks.models import Track
from playlists.models import Playlist

# Import serializers from separate apps
from artists.serializers import ArtistSerializer
from tracks.serializers import TrackSerializer
from playlists.serializers import PlaylistSerializer

# Configure logging
logger = logging.getLogger(__name__)

class GlobalSearchViewSet(viewsets.ViewSet):
    """
    Global search across all music-related models.
    This endpoint allows searching across tracks, artists, and playlists
    with a single query.
    """
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get('q', '')
        logger.debug(f"Search query: {query}")

        if not query:
            return Response({"error": "Missing search query"}, status=400)

        tracks = Track.objects.filter(Q(title__icontains=query))
        artists = Artist.objects.filter(Q(name__icontains=query))
        playlists = Playlist.objects.filter(Q(name__icontains=query))

        logger.debug(f"Search results - Tracks: {tracks.count()}, Artists: {artists.count()}, Playlists: {playlists.count()}")

        return Response({
            "tracks": TrackSerializer(tracks, many=True).data,
            "artists": ArtistSerializer(artists, many=True).data,
            "playlists": PlaylistSerializer(playlists, many=True).data
        })