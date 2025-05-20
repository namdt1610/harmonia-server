from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FavoriteViewSet

router = DefaultRouter()
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('favorites/tracks/<int:track_id>/', FavoriteViewSet.as_view({'post': 'add_track'})),
    path('', include(router.urls)),
] 