from rest_framework import viewsets, permissions
from .models import Artist
from .serializers import ArtistSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission

class ArtistViewSet(viewsets.ModelViewSet):
    """
    RESTful Artist management ViewSet.
    Provides comprehensive artist management functionality.
    """
    swagger_tags = ['Artists']
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.IsAuthenticated, HasCustomPermission]

    @property
    def required_permission(self):
        mapping = {
            'create': 'add_artist',
            'update': 'edit_artist',
            'partial_update': 'edit_artist',
            'destroy': 'delete_artist',
            'list': 'view_artist',
            'retrieve': 'view_artist'
        }
        return mapping.get(self.action)

    @swagger_auto_schema(
        tags=['Artists'],
        operation_description="Get a list of all artists",
        responses={
            200: ArtistSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Artists'],
        operation_description="Create a new artist",
        request_body=ArtistSerializer(),
        responses={
            201: ArtistSerializer(),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Artists'],
        operation_description="Get a specific artist by ID",
        responses={
            200: ArtistSerializer(),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Artists'],
        operation_description="Update an artist",
        request_body=ArtistSerializer(),
        responses={
            200: ArtistSerializer(),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Artists'],
        operation_description="Partially update an artist",
        request_body=ArtistSerializer(),
        responses={
            200: ArtistSerializer(),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Artists'],
        operation_description="Delete an artist",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs) 