from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .models import Profile
from .serializers import ProfileSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    RESTful User management ViewSet.
    Provides comprehensive user management functionality.
    """
    swagger_tags = ['Users']
    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated, HasCustomPermission]

    @property
    def required_permission(self):
        mapping = {
            'create': 'add_user',
            'update': 'edit_user',
            'partial_update': 'edit_user',
            'destroy': 'delete_user',
            'list': 'view_user',
            'retrieve': 'view_user'
        }
        return mapping.get(self.action)

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Get a list of all users",
        responses={
            200: ProfileSerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Create a new user",
        request_body=ProfileSerializer(),
        responses={
            201: ProfileSerializer(),
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Get a specific user by ID",
        responses={
            200: ProfileSerializer(),
            404: "Not Found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Update a user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties=ProfileSerializer()
        ),
        responses={
            200: openapi.Response(
                description="User updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties=ProfileSerializer()
                )
            ),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Delete a user",
        responses={
            204: "No Content",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Partially update a user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties=ProfileSerializer()
        ),
        responses={
            200: openapi.Response(
                description="User partially updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties=ProfileSerializer()
                )
            ),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

class ProfileViewSet(viewsets.ModelViewSet):
    """
    RESTful Profile management ViewSet.
    Provides comprehensive profile management functionality.
    """
    swagger_tags = ['Profiles']
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, HasCustomPermission]

    @property
    def required_permission(self):
        mapping = {
            'create': 'add_profile',
            'update': 'edit_profile',
            'partial_update': 'edit_profile',
            'destroy': 'delete_profile',
            'list': 'view_profile',
            'retrieve': 'view_profile'
        }
        return mapping.get(self.action)

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    @swagger_auto_schema(
        tags=['Profiles'],
        operation_description="Get the current user's profile",
        responses={
            200: ProfileSerializer(),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Profiles'],
        operation_description="Create a new profile",
        request_body=ProfileSerializer(),
        responses={
            201: ProfileSerializer(),
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Profiles'],
        operation_description="Get a specific profile by ID",
        responses={
            200: ProfileSerializer(),
            404: "Not Found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Profiles'],
        operation_description="Update a profile",
        request_body=ProfileSerializer(),
        responses={
            200: ProfileSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Profiles'],
        operation_description="Delete a profile",
        responses={
            204: "No Content",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Profiles'],
        operation_description="Partially update a profile",
        request_body=ProfileSerializer(),
        responses={
            200: ProfileSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

