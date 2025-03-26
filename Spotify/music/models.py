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


class Track(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True, related_name="tracks")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="tracks")
    file = models.FileField(upload_to="tracks/", validators=[validate_audio_file], max_length=500)
    music_video = models.FileField(upload_to="music_videos/", blank=True, null=True, validators=[validate_audio_file], max_length=500)
    duration = models.PositiveIntegerField(help_text="Duration in seconds", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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


class Playlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playlists")
    name = models.CharField(max_length=255, db_index=True)
    tracks = models.ManyToManyField(Track, related_name="playlists")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user.username})"
