from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.get_overview, name='analytics-overview'),
    path('dashboard/', views.get_dashboard_stats, name='analytics-dashboard'),
    path('plays/', views.get_play_stats, name='analytics-plays'),
    path('users/', views.get_user_stats, name='analytics-users'),
] 