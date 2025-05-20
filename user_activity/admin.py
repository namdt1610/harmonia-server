from django.contrib import admin
from .models import UserActivity, PlayHistory

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'track', 'playlist', 'timestamp')
    list_filter = ('action', 'user', 'timestamp')
    search_fields = ('user__username', 'track__title', 'playlist__name')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

@admin.register(PlayHistory)
class PlayHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'track', 'played_at')
    list_filter = ('user', 'played_at')
    search_fields = ('user__username', 'track__title')
    readonly_fields = ('played_at',)
    ordering = ('-played_at',) 