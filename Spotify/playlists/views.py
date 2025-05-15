from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Count
from music.models import Track
from .models import Playlist
from .serializers import PlaylistSerializer

class PlaylistViewSet(viewsets.ModelViewSet):
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
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
            
        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        playlist = serializer.save()
        # Invalidate user's playlist cache
        cache.delete(f'playlist_list_{self.request.user.id}')

    def perform_update(self, serializer):
        playlist = serializer.save()
        # Invalidate user's playlist cache
        cache.delete(f'playlist_list_{self.request.user.id}')

    def perform_destroy(self, instance):
        instance.delete()
        # Invalidate user's playlist cache
        cache.delete(f'playlist_list_{self.request.user.id}')

    @action(detail=False)
    def featured(self, request):
        """Get featured playlists"""
        cache_key = 'featured_playlists'
        cached_playlists = cache.get(cache_key)
        
        if cached_playlists is None:
            # Get public playlists with most tracks
            playlists = Playlist.objects.filter(is_public=True).annotate(
                track_count=Count('tracks')
            ).order_by('-track_count')[:10]
            cached_playlists = self.get_serializer(playlists, many=True).data
            cache.set(cache_key, cached_playlists, 1800)  # 30 minutes cache
            
        return Response(cached_playlists)

    @action(detail=True, methods=['post'],url_path='add-track/(?P<track_id>[^/.]+)')
    def add_track(self, request, pk=None, track_id=None):
        try:
            playlist = Playlist.objects.get(id=pk)
            track = Track.objects.get(id=track_id)
            playlist.tracks.add(track)
            playlist.save()
            return Response({'status': 'track added'}, status=status.HTTP_200_OK)
        except Playlist.DoesNotExist:
            return Response({'error': 'Playlist not found'}, status=status.HTTP_404_NOT_FOUND)
        except Track.DoesNotExist:
            return Response({'error': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)

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