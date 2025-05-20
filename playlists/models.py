from django.db import models
from django.contrib.auth.models import User
from tracks.models import Track

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playlists")
    name = models.CharField(max_length=255, db_index=True)
    tracks = models.ManyToManyField(Track, related_name="playlists")
    created_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=True)
    followers = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class PlaylistTrack(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'added_at']
        unique_together = ['playlist', 'track'] 