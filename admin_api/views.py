from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg
from user.serializers import ProfileSerializer
from tracks.models import Track
from albums.models import Album
from artists.models import Artist
from playlists.models import Playlist
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from user_activity.models import UserActivity
from search.models import SearchHistory
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from permissions.permissions import HasCustomPermission, has_permission
from rest_framework.permissions import IsAuthenticated

User = get_user_model()

# Create your views here.

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing users.
    Provides comprehensive user management functionality for administrators.
    """
    swagger_tags = ['Admin']
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
            'retrieve': 'view_user',
        }
        return mapping.get(self.action)

    @swagger_auto_schema(
        tags=['Admin'],
        operation_description="Get a list of all users",
        responses={
            200: ProfileSerializer(many=True),
            401: "Unauthorized",
            403: "Forbidden - Admin access required"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin'],
        operation_description="Create a new user",
        request_body=ProfileSerializer(),
        responses={
            201: ProfileSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden - Admin access required"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin'],
        operation_description="Get a specific user by ID",
        responses={
            200: ProfileSerializer(),
            404: "Not Found",
            401: "Unauthorized",
            403: "Forbidden - Admin access required"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin'],
        operation_description="Update a user",
        request_body=ProfileSerializer(),
        responses={
            200: ProfileSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden - Admin access required",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Only allow updating role
        role = request.data.get('role')
        if role is not None:
            instance.role = role
            instance.save(update_fields=['role'])
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return Response({'error': 'Only role can be updated'}, status=400)

    @swagger_auto_schema(
        tags=['Admin'],
        operation_description="Partially update a user",
        request_body=ProfileSerializer(),
        responses={
            200: ProfileSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden - Admin access required",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Admin'],
        operation_description="Delete a user",
        responses={
            204: "No Content",
            401: "Unauthorized",
            403: "Forbidden - Admin access required",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

@swagger_auto_schema(
    method='get',
    tags=['Admin'],
    operation_description="Get overview analytics data for admin dashboard",
    responses={
        200: openapi.Response(
            description="Analytics overview data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'totalUsers': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'totalTracks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'totalAlbums': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'totalPlaylists': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'totalArtists': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'newUsersLastMonth': openapi.Schema(type=openapi.TYPE_INTEGER)
                }
            )
        ),
        401: "Unauthorized",
        403: "Forbidden - Admin access required"
    }
)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasCustomPermission])
def analytics_overview(request):
    """Get overview analytics data for admin dashboard"""
    if not has_permission(request.user, 'view_analytics'):
        return Response({"error": "Permission denied"}, status=403)
        
    total_users = User.objects.count()
    total_tracks = Track.objects.count()
    total_albums = Album.objects.count()
    total_playlists = Playlist.objects.count()
    total_artists = Artist.objects.count()
    
    # New users in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_last_month = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    return Response({
        'totalUsers': total_users,
        'totalTracks': total_tracks,
        'totalAlbums': total_albums,
        'totalPlaylists': total_playlists,
        'totalArtists': total_artists,
        'newUsersLastMonth': new_users_last_month
    })

@swagger_auto_schema(
    method='get',
    tags=['Admin'],
    operation_description="Get detailed user analytics",
    responses={
        200: openapi.Response(
            description="User analytics data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'userGrowth': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'activeUsers': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'activityTypes': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )
        ),
        401: "Unauthorized",
        403: "Forbidden - Admin access required"
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasCustomPermission])
def user_analytics(request):
    """Get detailed user analytics"""
    if not has_permission(request.user, 'view_analytics'):
        return Response({"error": "Permission denied"}, status=403)
        
    # User growth over time
    thirty_days_ago = timezone.now() - timedelta(days=30)
    user_growth = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(date_joined)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Active users (users with activity in last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    active_users = UserActivity.objects.filter(
        timestamp__gte=seven_days_ago
    ).values('user').distinct().count()
    
    # User activity types
    activity_types = UserActivity.objects.values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    return Response({
        'userGrowth': list(user_growth),
        'activeUsers': active_users,
        'activityTypes': list(activity_types)
    })

@swagger_auto_schema(
    method='get',
    tags=['Admin'],
    operation_description="Get content-related analytics",
    responses={
        200: openapi.Response(
            description="Content analytics data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'topTracks': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'topDownloads': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'topArtists': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'topAlbums': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )
        ),
        401: "Unauthorized",
        403: "Forbidden - Admin access required"
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasCustomPermission])
def content_analytics(request):
    """Get content-related analytics"""
    if not has_permission(request.user, 'view_analytics'):
        return Response({"error": "Permission denied"}, status=403)
        
    # Most played tracks
    top_tracks = Track.objects.annotate(
        total_plays=Sum('play_count')
    ).order_by('-total_plays')[:10]
    
    # Most downloaded tracks
    top_downloads = Track.objects.annotate(
        total_downloads=Sum('download_count')
    ).order_by('-total_downloads')[:10]
    
    # Most popular artists
    top_artists = Artist.objects.annotate(
        track_count=Count('tracks'),
        total_plays=Sum('tracks__play_count')
    ).order_by('-total_plays')[:10]
    
    # Most popular albums
    top_albums = Album.objects.annotate(
        track_count=Count('tracks'),
        total_plays=Sum('tracks__play_count')
    ).order_by('-total_plays')[:10]
    
    return Response({
        'topTracks': [
            {
                'id': track.id,
                'title': track.title,
                'artist': track.artist.name,
                'plays': track.total_plays
            } for track in top_tracks
        ],
        'topDownloads': [
            {
                'id': track.id,
                'title': track.title,
                'artist': track.artist.name,
                'downloads': track.total_downloads
            } for track in top_downloads
        ],
        'topArtists': [
            {
                'id': artist.id,
                'name': artist.name,
                'trackCount': artist.track_count,
                'totalPlays': artist.total_plays
            } for artist in top_artists
        ],
        'topAlbums': [
            {
                'id': album.id,
                'title': album.title,
                'artist': album.artist.name,
                'trackCount': album.track_count,
                'totalPlays': album.total_plays
            } for album in top_albums
        ]
    })

@swagger_auto_schema(
    method='get',
    tags=['Admin'],
    operation_description="Get search-related analytics",
    responses={
        200: openapi.Response(
            description="Search analytics data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'topSearches': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'searchTrends': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'averageResults': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            )
        ),
        401: "Unauthorized",
        403: "Forbidden - Admin access required"
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasCustomPermission])
def search_analytics(request):
    """Get search-related analytics"""
    if not has_permission(request.user, 'view_analytics'):
        return Response({"error": "Permission denied"}, status=403)
        
    # Most common search terms
    top_searches = SearchHistory.objects.values('query').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    # Search trends over time
    thirty_days_ago = timezone.now() - timedelta(days=30)
    search_trends = SearchHistory.objects.filter(
        timestamp__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(timestamp)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Average results per search
    avg_results = SearchHistory.objects.aggregate(
        avg_results=Avg('result_count')
    )
    
    return Response({
        'topSearches': list(top_searches),
        'searchTrends': list(search_trends),
        'averageResults': avg_results['avg_results']
    })

@swagger_auto_schema(
    method='get',
    tags=['Admin'],
    operation_description="Get detailed activity analytics",
    responses={
        200: openapi.Response(
            description="Activity analytics data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'activityTrends': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'activityByType': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'peakHours': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                }
            )
        ),
        401: "Unauthorized",
        403: "Forbidden - Admin access required"
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, HasCustomPermission])
def activity_analytics(request):
    """Get detailed activity analytics"""
    if not has_permission(request.user, 'view_analytics'):
        return Response({"error": "Permission denied"}, status=403)
        
    # Activity over time
    thirty_days_ago = timezone.now() - timedelta(days=30)
    activity_trends = UserActivity.objects.filter(
        timestamp__gte=thirty_days_ago
    ).extra(
        select={'day': 'date(timestamp)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Activity by type
    activity_by_type = UserActivity.objects.values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Peak activity hours
    peak_hours = UserActivity.objects.extra(
        select={'hour': 'extract(hour from timestamp)'}
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count')[:24]
    
    return Response({
        'activityTrends': list(activity_trends),
        'activityByType': list(activity_by_type),
        'peakHours': list(peak_hours)
    })
