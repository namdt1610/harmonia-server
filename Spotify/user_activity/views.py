from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import UserActivity
from .serializers import UserActivitySerializer

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent activities"""
        activities = self.get_queryset().order_by('-timestamp')[:20]
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
    
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