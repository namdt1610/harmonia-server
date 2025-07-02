from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import QueueViewSet

router = DefaultRouter()
router.register(r'queue', QueueViewSet, basename='queue')

# Additional URL patterns for stream-queue endpoints
urlpatterns = [
    # Standard queue endpoints
    path('', include(router.urls)),
    
    # Stream-queue specific endpoints for frontend compatibility
    path('stream-queue/next/', QueueViewSet.as_view({'post': 'next_track'}), name='stream-queue-next'),
    path('stream-queue/previous/', QueueViewSet.as_view({'post': 'previous_track'}), name='stream-queue-previous'),
] 