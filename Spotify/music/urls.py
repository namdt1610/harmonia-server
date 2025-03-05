from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArtistViewSet, AlbumViewSet, TrackViewSet, PlaylistViewSet, UploadTrackViewSet

router = DefaultRouter()
router.register(r'artists', ArtistViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'playlists', PlaylistViewSet)
router.register(r'upload-tracks', UploadTrackViewSet, basename='upload-track')

urlpatterns = [
    path('', include(router.urls)),
]
