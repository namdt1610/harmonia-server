from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F
from .models import Track
from .serializers import TrackSerializer

class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Track.objects.all()
        genre = self.request.query_params.get('genre', None)
        artist = self.request.query_params.get('artist', None)
        album = self.request.query_params.get('album', None)
        search = self.request.query_params.get('search', None)
        
        if genre:
            queryset = queryset.filter(genres__name__icontains=genre)
        if artist:
            queryset = queryset.filter(artist__name__icontains=artist)
        if album:
            queryset = queryset.filter(album__title__icontains=album)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset.distinct()
    
    @action(detail=True, methods=['post'])
    def increment_play_count(self, request, pk=None):
        track = self.get_object()
        track.increment_play_count()
        return Response({'status': 'play count incremented'})
    
    @action(detail=True, methods=['post'])
    def increment_download_count(self, request, pk=None):
        track = self.get_object()
        track.increment_download_count()
        return Response({'status': 'download count incremented'})
    
    @action(detail=False, methods=['get'])
    def top_tracks(self, request):
        top_tracks = Track.objects.annotate(
            total_plays=F('play_count') + F('download_count')
        ).order_by('-total_plays')[:10]
        serializer = self.get_serializer(top_tracks, many=True)
        return Response(serializer.data) 