from django.contrib import admin
from .models import Track

@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'album', 'duration', 'play_count', 'download_count', 'is_downloadable')
    list_filter = ('is_downloadable', 'artist', 'album', 'genres')
    search_fields = ('title', 'artist__name', 'album__title')
    filter_horizontal = ('genres',) 