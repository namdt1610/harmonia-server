from django.contrib import admin
from .models import Favorite

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'get_content', 'created_at')
    list_filter = ('content_type', 'user', 'created_at')
    search_fields = ('user__username', 'track__title', 'artist__name', 'album__title', 'playlist__name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def get_content(self, obj):
        return obj.track or obj.artist or obj.album or obj.playlist
    get_content.short_description = 'Content' 