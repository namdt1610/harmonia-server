from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Artist(models.Model):
    name = models.CharField(max_length=255)
    bio = models.TextField(blank=True, null=True, default='No bio available')
    avatar = models.ImageField(upload_to='artists/', blank=True, null=True)

    def __str__(self):
        return self.name

class Album(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
    release_date = models.DateField()
    cover = models.ImageField(upload_to='albums/', blank=True, null=True)

    def __str__(self):
        return self.title

def validate_audio_file(file):
    if file.size > 50 * 1024 * 1024:
        raise ValidationError("File must be less than 50Mb.")

class Track(models.Model):
    title = models.CharField(max_length=255)
    album = models.ForeignKey(Album, on_delete=models.SET_NULL,null=True, blank=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='tracks')
    file = models.FileField(upload_to='tracks/',validators=[validate_audio_file], max_length=500)
    duration = models.PositiveIntegerField(help_text="Duration in minutes", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.album and self.album.artist != self.artist:
            raise ValueError("Artist of the album and artist of the track must be the same")
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.title + ' - ' + self.artist.name

class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    tracks = models.ManyToManyField(Track, related_name='playlists')

    def __str__(self):
        return self.name
