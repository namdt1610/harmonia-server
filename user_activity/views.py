from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import UserActivity
from .serializers import UserActivitySerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    RESTful User Activity management ViewSet.
    Provides comprehensive user activity tracking and statistics functionality.
    """
    swagger_tags = ['User Activities']
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated, HasCustomPermission]
    
    @property
    def required_permission(self):
        mapping = {
            'list': 'view_useractivity',
            'retrieve': 'view_useractivity'
        }
        return mapping.get(self.action)
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        tags=['User Activities'],
        operation_description="Get a list of all user activities",
        responses={
            200: UserActivitySerializer(many=True),
            401: "Unauthorized"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['User Activities'],
        operation_description="Get a specific activity by ID",
        responses={
            200: openapi.Response(
                description="User activity details",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'action': openapi.Schema(type=openapi.TYPE_STRING),
                        'track': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                    }
                )
            ),
            404: "Not Found",
            401: "Unauthorized"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['User Activities'],
        operation_description="Get recent activities (last 20)",
        responses={
            200: openapi.Response(
                description="List of recent activities",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'user': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'action': openapi.Schema(type=openapi.TYPE_STRING),
                            'track': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
                            'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                        }
                    )
                )
            ),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent activities"""
        activities = self.get_queryset().order_by('-timestamp')[:20]
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        tags=['User Activities'],
        operation_description="Get user activity statistics for the last 30 days",
        responses={
            200: openapi.Response(
                description="User activity statistics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'activity_counts': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'action': openapi.Schema(type=openapi.TYPE_STRING),
                                    'count': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        ),
                        'most_played_tracks': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'track__title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'count': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        )
                    }
                )
            ),
            401: "Unauthorized"
        }
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user activity statistics"""
        # Get activities from the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_activities = self.get_queryset().filter(timestamp__gte=thirty_days_ago)
        
        # Count activities by type
        activity_counts = recent_activities.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Get most played tracks
        most_played = recent_activities.filter(action='play').values(
            'track__title'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return Response({
            'activity_counts': activity_counts,
            'most_played_tracks': most_played
        }) 