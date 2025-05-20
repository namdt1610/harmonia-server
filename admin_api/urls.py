from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminUserViewSet,
    analytics_overview,
    user_analytics,
    content_analytics,
    search_analytics,
    activity_analytics
)

router = DefaultRouter()
router.register(r'users', AdminUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/overview/', analytics_overview, name='analytics-overview'),
    path('analytics/users/', user_analytics, name='user-analytics'),
    path('analytics/content/', content_analytics, name='content-analytics'),
    path('analytics/search/', search_analytics, name='search-analytics'),
    path('analytics/activity/', activity_analytics, name='activity-analytics'),
] 