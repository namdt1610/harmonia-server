from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Count

from permissions.permissions import HasCustomPermission
from .models import Genre
from .serializers import GenreSerializer

class GenreViewSet(viewsets.ModelViewSet):
    """
    RESTful Genre management ViewSet.
    Provides comprehensive genre management functionality.
    """
    swagger_tags = ['Genres']
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated, HasCustomPermission]
    
    @property
    def required_permission(self):
        mapping = {
            'create': 'add_genre',
            'update': 'edit_genre',
            'partial_update': 'edit_genre',
            'destroy': 'delete_genre',
            'list': 'view_genre',
            'retrieve': 'view_genre'
        }
        return mapping.get(self.action)
    
    def get_queryset(self):
        queryset = Genre.objects.all()
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        return queryset

    @swagger_auto_schema(
        tags=['Genres'],
        operation_description="Get a list of all genres",
        responses={
            200: GenreSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Genres'],
        operation_description="Create a new genre",
        request_body=GenreSerializer(),
        responses={
            201: GenreSerializer(),
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Genres'],
        operation_description="Get a specific genre by ID",
        responses={
            200: GenreSerializer(),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Genres'],
        operation_description="Update a genre",
        request_body=GenreSerializer(),
        responses={
            200: GenreSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Genres'],
        operation_description="Delete a genre",
        responses={
            204: "No Content",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Genres'],
        operation_description="Partially update a genre",
        request_body=GenreSerializer(),
        responses={
            200: GenreSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Genres'],
        operation_description="Get genres with most tracks",
        responses={
            200: GenreSerializer(many=True),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get genres with most tracks"""
        genres = Genre.objects.annotate(
            track_count=Count('tracks')
        ).order_by('-track_count')[:10]
        serializer = self.get_serializer(genres, many=True)
        return Response(serializer.data) 