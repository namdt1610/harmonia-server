from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg
from rest_framework.permissions import IsAdminUser
from user.models import Profile
from user.serializers import UserSerializer
from music.models import Track, Album, Artist, Playlist
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from user_activity.models import UserActivity
from search.models import SearchHistory

User = get_user_model()

# Create your views here.

class AdminUserViewSet(viewsets.ModelViewSet):
    """ViewSet for admin to manage users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics_overview(request):
    """Get overview analytics data for admin dashboard"""
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

@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_analytics(request):
    """Get detailed user analytics"""
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

@api_view(['GET'])
@permission_classes([IsAdminUser])
def content_analytics(request):
    """Get content-related analytics"""
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

@api_view(['GET'])
@permission_classes([IsAdminUser])
def search_analytics(request):
    """Get search-related analytics"""
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

@api_view(['GET'])
@permission_classes([IsAdminUser])
def activity_analytics(request):
    """Get detailed activity analytics"""
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
