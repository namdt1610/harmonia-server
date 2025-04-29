from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArtistViewSet, AlbumViewSet, TrackViewSet, PlaylistViewSet, UploadTrackViewSet, GlobalSearchViewSet, FavoriteViewSet, GenreViewSet, UserActivityViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'', GlobalSearchViewSet, basename='search')
router.register(r'artists', ArtistViewSet)
router.register(r'albums', AlbumViewSet)
router.register(r'tracks', TrackViewSet)
router.register(r'upload-tracks', UploadTrackViewSet, basename='upload-track')
router.register(r'playlists', PlaylistViewSet)
router.register(r'favorites', FavoriteViewSet, basename='favorites')
router.register(r'genres', GenreViewSet, basename='genres')
router.register(r'user-activity', UserActivityViewSet, basename='user-activity')

urlpatterns = [
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)