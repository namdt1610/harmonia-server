from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist
from user.models import User
from user_activity.models import PlayHistory

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_overview(request):
    """Get overview statistics for the admin dashboard"""
    total_artists = Artist.objects.count()
    total_albums = Album.objects.count()
    total_tracks = Track.objects.count()
    total_playlists = Playlist.objects.count()
    total_users = User.objects.count()
    total_plays = PlayHistory.objects.count()

    return Response({
        'totalArtists': total_artists,
        'totalAlbums': total_albums,
        'totalTracks': total_tracks,
        'totalPlaylists': total_playlists,
        'totalUsers': total_users,
        'totalPlays': total_plays
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_dashboard_stats(request):
    """Get detailed dashboard statistics"""
    # Recent tracks with play counts
    recent_tracks = Track.objects.annotate(
        plays=Count('play_history')
    ).order_by('-created_at')[:10].values('id', 'title', 'artist__name', 'plays')

    # Top artists by plays
    top_artists = Artist.objects.annotate(
        plays=Count('tracks__play_history')
    ).order_by('-plays')[:10].values('id', 'name', 'plays')

    # Top albums by plays
    top_albums = Album.objects.annotate(
        plays=Count('tracks__play_history')
    ).order_by('-plays')[:10].values('id', 'title', 'artist__name', 'plays')

    # Top playlists by followers
    top_playlists = Playlist.objects.order_by('-followers')[:10].values(
        'id', 'name', 'followers'
    )

    return Response({
        'recentTracks': list(recent_tracks),
        'topArtists': list(top_artists),
        'topAlbums': list(top_albums),
        'topPlaylists': list(top_playlists)
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_play_stats(request):
    """Get play statistics for a given period"""
    period = request.GET.get('period', 'day')
    now = timezone.now()

    if period == 'day':
        start_date = now - timedelta(days=7)
        interval = 'hour'
    elif period == 'week':
        start_date = now - timedelta(weeks=4)
        interval = 'day'
    elif period == 'month':
        start_date = now - timedelta(days=180)
        interval = 'week'
    else:  # year
        start_date = now - timedelta(days=365)
        interval = 'month'

    plays = PlayHistory.objects.filter(
        played_at__gte=start_date
    ).extra(
        select={'date': f"date_trunc('{interval}', played_at)"}
    ).values('date').annotate(
        plays=Count('id')
    ).order_by('date')

    return Response(list(plays))

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_user_stats(request):
    """Get user statistics for a given period"""
    period = request.GET.get('period', 'day')
    now = timezone.now()

    if period == 'day':
        start_date = now - timedelta(days=7)
        interval = 'hour'
    elif period == 'week':
        start_date = now - timedelta(weeks=4)
        interval = 'day'
    elif period == 'month':
        start_date = now - timedelta(days=180)
        interval = 'week'
    else:  # year
        start_date = now - timedelta(days=365)
        interval = 'month'

    # New users
    new_users = User.objects.filter(
        date_joined__gte=start_date
    ).extra(
        select={'date': f"date_trunc('{interval}', date_joined)"}
    ).values('date').annotate(
        new_users=Count('id')
    ).order_by('date')

    # Active users (users who have played tracks)
    active_users = PlayHistory.objects.filter(
        played_at__gte=start_date
    ).extra(
        select={'date': f"date_trunc('{interval}', played_at)"}
    ).values('date').annotate(
        active_users=Count('user', distinct=True)
    ).order_by('date')

    # Combine the results
    stats = []
    for date in set(new_users.values_list('date', flat=True)):
        new_users_count = new_users.filter(date=date).first()['new_users'] if new_users.filter(date=date).exists() else 0
        active_users_count = active_users.filter(date=date).first()['active_users'] if active_users.filter(date=date).exists() else 0
        
        stats.append({
            'date': date,
            'newUsers': new_users_count,
            'activeUsers': active_users_count
        })

    return Response(sorted(stats, key=lambda x: x['date'])) 