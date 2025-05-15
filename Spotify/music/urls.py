from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ArtistViewSet, AlbumViewSet, TrackViewSet, PlaylistViewSet,
    GenreViewSet, GlobalSearchViewSet, UploadTrackViewSet,
    UserActivityViewSet
)
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'artists', ArtistViewSet, basename='artist')
router.register(r'albums', AlbumViewSet, basename='album')
router.register(r'tracks', TrackViewSet, basename='track')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'playlists', PlaylistViewSet, basename='playlists')
router.register(r'', GlobalSearchViewSet, basename='search')
router.register(r'upload', UploadTrackViewSet, basename='upload')
router.register(r'activities', UserActivityViewSet, basename='activities')

urlpatterns = [
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)