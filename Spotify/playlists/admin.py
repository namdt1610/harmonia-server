from django.contrib import admin
from .models import Playlist, PlaylistTrack

class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    extra = 1

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'created_at')
    list_filter = ('is_public', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    inlines = [PlaylistTrackInline]

    def tracks_count(self, obj):
        return obj.tracks.count()
    tracks_count.short_description = 'Tracks' 