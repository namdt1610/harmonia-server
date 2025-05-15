from django.db import models
from django.conf import settings
from tracks.models import Track
from playlists.models import Playlist

class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('play', 'Play'),
        ('download', 'Download'),
        ('create_playlist', 'Create Playlist'),
        ('update_playlist', 'Update Playlist'),
        ('delete_playlist', 'Delete Playlist'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    track = models.ForeignKey(Track, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
        verbose_name_plural = 'User Activities'

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}" 