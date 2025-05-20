from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Genre
from .serializers import GenreSerializer

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Genre.objects.all()
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get genres with most tracks"""
        genres = Genre.objects.annotate(
            track_count=Count('tracks')
        ).order_by('-track_count')[:10]
        serializer = self.get_serializer(genres, many=True)
        return Response(serializer.data) 