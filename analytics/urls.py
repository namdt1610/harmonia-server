from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.get_overview, name='analytics-overview'),
    path('dashboard-stats/', views.get_dashboard_stats, name='analytics-dashboard-stats'),
    path('plays-stats/', views.get_play_stats, name='analytics-plays-stats'),
    path('users-stats/', views.get_user_stats, name='analytics-users-stats'),
] 