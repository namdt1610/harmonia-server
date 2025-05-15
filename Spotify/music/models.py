from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Artist(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    bio = models.TextField(blank=True, null=True, default='No bio available')
    avatar = models.ImageField(upload_to='artists/', blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Album(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="albums")
    release_date = models.DateField(default=None, blank=True, null=True)
    cover = models.ImageField(upload_to="albums/", blank=True, null=True)

    class Meta:
        ordering = ["-release_date"]
        unique_together = ("title", "artist")  # Một artist không có 2 album trùng tên

    def __str__(self):
        return f"{self.title} - {self.artist.name}"


def validate_audio_file(file):
    """ Giới hạn dung lượng file audio tối đa là 50MB """
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size > max_size:
        raise ValidationError("File must be less than 50MB.")
    
class Genre(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Track(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True, related_name="tracks")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="tracks")
    file = models.FileField(upload_to="tracks/", validators=[validate_audio_file], max_length=500)
    music_video = models.FileField(upload_to="music_videos/",default='No video available', blank=True, null=True, validators=[validate_audio_file], max_length=500)
    duration = models.PositiveIntegerField(help_text="Duration in seconds", null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name="tracks", blank=True)
    lyrics = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    play_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    is_downloadable = models.BooleanField(default=True)
    track_thumbnail = models.ImageField(upload_to="track_thumbnails/", blank=True, null=True)
    video_thumbnail = models.ImageField(upload_to="video_thumbnails/", blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["artist"]),
            models.Index(fields=["album"]),
        ]
        ordering = ["-created_at"]  # Bài hát mới nhất lên trước

    def clean(self):
        """ Kiểm tra nếu album có artist khác với artist của track """
        if self.album and self.album.artist != self.artist:
            raise ValidationError("Artist of the album and artist of the track must be the same.")

    def save(self, *args, **kwargs):
        self.clean()  # Gọi clean() để validate trước khi save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.artist.name}"
    
    def increment_play_count(self):
        self.play_count += 1
        self.save(update_fields=['play_count'])
    
    def increment_download_count(self):
        self.download_count += 1  
        self.save(update_fields=['download_count'])


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playlists")
    name = models.CharField(max_length=255, db_index=True)
    tracks = models.ManyToManyField(Track, related_name="playlists")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

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