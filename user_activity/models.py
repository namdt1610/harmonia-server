from django.db import models
from django.contrib.auth.models import User
from tracks.models import Track
from playlists.models import Playlist

class UserActivity(models.Model):
    ACTION_CHOICES = (
        ('play', 'Played'),
        ('download', 'Downloaded'),
        ('like', 'Liked'),
        ('add_to_playlist', 'Added to Playlist'),
        ('create_playlist', 'Created Playlist'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        action_label = dict(self.ACTION_CHOICES).get(self.action, self.action)
        if self.track:
            return f"{self.user.username} {action_label} {self.track.title}"
        elif self.playlist:
            return f"{self.user.username} {action_label} {self.playlist.name}"
        return f"{self.user.username} {action_label}"

class PlayHistory(models.Model):
    """
    Model to track when users play tracks.
    Used for analytics and play count tracking.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='play_history')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='play_history')
    played_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-played_at']
        verbose_name_plural = 'Play histories'
    
    def __str__(self):
        return f"{self.user.username} played {self.track.title} at {self.played_at.strftime('%Y-%m-%d %H:%M')}" 