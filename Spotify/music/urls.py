from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArtistViewSet, AlbumViewSet, TrackViewSet, PlaylistViewSet, UploadTrackViewSet, GlobalSearchViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'artists', ArtistViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'playlists', PlaylistViewSet)
router.register(r'upload-tracks', UploadTrackViewSet, basename='upload-track')
router.register(r'', GlobalSearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)