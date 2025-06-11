from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .models import Album
from .serializers import AlbumSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission

class AlbumViewSet(viewsets.ModelViewSet):
    """
    RESTful Album management ViewSet.
    Provides comprehensive album management functionality including filtering, searching,
    and retrieving popular/latest albums.
    """
    swagger_tags = ['Albums']
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [permissions.IsAuthenticated, HasCustomPermission]
    
    @property
    def required_permission(self):
        mapping = {
            'create': 'add_album',
            'update': 'edit_album',
            'partial_update': 'edit_album',
            'destroy': 'delete_album',
            'list': 'view_album',
            'retrieve': 'view_album',
            'by_artist': 'view_album'
        }
        return mapping.get(self.action)
    
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
    
    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Get albums by artist ID",
        responses={
            200: AlbumSerializer(many=True),
            400: "Bad Request - artist_id parameter is required"
        }
    )
    @action(detail=False, methods=['get'])
    def by_artist(self, request):
        artist_id = request.query_params.get('artist_id')
        if artist_id:
            albums = Album.objects.filter(artist_id=artist_id)
            serializer = self.get_serializer(albums, many=True)
            return Response(serializer.data)
        return Response({"error": "artist_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Get latest albums",
        responses={
            200: openapi.Response(
                description="List of latest albums",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                            'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                        }
                    )
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest albums"""
        albums = Album.objects.order_by('-release_date')[:10]
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Get popular albums (albums with most tracks)",
        responses={
            200: openapi.Response(
                description="List of popular albums",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                            'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'track_count': openapi.Schema(type=openapi.TYPE_INTEGER)
                        }
                    )
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get albums with most tracks"""
        albums = Album.objects.annotate(
            track_count=Count('tracks')
        ).order_by('-track_count')[:10]
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Get a list of all albums",
        responses={
            200: openapi.Response(
                description="List of albums",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                            'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                        }
                    )
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Create a new album",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'artist'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
            }
        ),
        responses={
            201: openapi.Response(
                description="Album created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Get a specific album by ID",
        responses={
            200: openapi.Response(
                description="Album details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                    }
                )
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Update an album",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
            }
        ),
        responses={
            200: openapi.Response(
                description="Album updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                    }
                )
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Delete an album",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Albums'],
        operation_description="Partially update an album",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING),
                'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
            }
        ),
        responses={
            200: openapi.Response(
                description="Album partially updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                        'artist': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'release_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                        'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format='uri'),
                        'description': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                    }
                )
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs) 