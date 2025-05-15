from django.contrib import admin
from .models import Genre

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'tracks_count', 'albums_count')
    search_fields = ('name', 'description')
    
    def tracks_count(self, obj):
        return obj.tracks.count()
    tracks_count.short_description = 'Tracks'
    
    def albums_count(self, obj):
        return obj.albums.count()
    albums_count.short_description = 'Albums' 