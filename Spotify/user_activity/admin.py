from django.contrib import admin
from .models import UserActivity

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'track', 'playlist', 'timestamp')
    list_filter = ('action', 'user', 'timestamp')
    search_fields = ('user__username', 'track__title', 'playlist__name')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',) 