from django.db import models
from django.conf import settings
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist

class Favorite(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('track', 'Track'),
        ('artist', 'Artist'),
        ('album', 'Album'),
        ('playlist', 'Playlist'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    track = models.ForeignKey(Track, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites')
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, null=True, blank=True, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['content_type']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
        unique_together = [
            ('user', 'track'),
            ('user', 'artist'),
            ('user', 'album'),
            ('user', 'playlist'),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        # Ensure exactly one content object is set
        content_objects = [self.track, self.artist, self.album, self.playlist]
        if content_objects.count(None) != 3:
            raise ValidationError("Exactly one content object must be set")
        
        # Ensure content_type matches the set object
        if self.track and self.content_type != 'track':
            raise ValidationError("Content type must match the set object")
        if self.artist and self.content_type != 'artist':
            raise ValidationError("Content type must match the set object")
        if self.album and self.content_type != 'album':
            raise ValidationError("Content type must match the set object")
        if self.playlist and self.content_type != 'playlist':
            raise ValidationError("Content type must match the set object")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        content = self.track or self.artist or self.album or self.playlist
        return f"{self.user.username} - {self.content_type} - {content}" 