from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Album
from .serializers import AlbumSerializer

class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Album.objects.all()
        artist = self.request.query_params.get('artist', None)
        genre = self.request.query_params.get('genre', None)
        search = self.request.query_params.get('search', None)
        
        if artist:
            queryset = queryset.filter(artist__name__icontains=artist)
        if genre:
            queryset = queryset.filter(genres__name__icontains=genre)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset.distinct()
    
    @action(detail=False, methods=['get'])
    def by_artist(self, request):
        artist_id = request.query_params.get('artist_id')
        if artist_id:
            albums = Album.objects.filter(artist_id=artist_id)
            serializer = self.get_serializer(albums, many=True)
            return Response(serializer.data)
        return Response({"error": "artist_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest albums"""
        albums = Album.objects.order_by('-release_date')[:10]
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get albums with most tracks"""
        albums = Album.objects.annotate(
            track_count=Count('tracks')
        ).order_by('-track_count')[:10]
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data) 