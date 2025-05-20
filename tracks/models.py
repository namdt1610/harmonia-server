from django.db import models
from django.core.exceptions import ValidationError
from artists.models import Artist
from albums.models import Album
from genres.models import Genre
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from django.core.files.base import ContentFile

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
    video = models.FileField(upload_to='videos/', null=True, blank=True)
    duration = models.PositiveIntegerField(help_text="Duration in seconds", null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name="tracks", blank=True)
    lyrics = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
        ordering = ["-created_at"]

    def clean(self):
        if self.album and self.album.artist != self.artist:
            raise ValidationError("Artist of the album and artist of the track must be the same.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Tự động lấy cover nếu chưa có thumbnail và có file audio
        if self.file and not self.track_thumbnail:
            try:
                audio = MP3(self.file.path, ID3=ID3)
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):  # APIC = Attached Picture
                        image_data = tag.data
                        self.track_thumbnail.save(
                            f"{self.id}_cover.jpg",
                            ContentFile(image_data),
                            save=True
                        )
                        break
            except Exception as e:
                print(f"Không thể lấy cover từ file audio: {e}")

    def __str__(self):
        return f"{self.title} - {self.artist.name}"
    
    def increment_play_count(self):
        self.play_count += 1
        self.save(update_fields=['play_count'])
    
    def increment_download_count(self):
        self.download_count += 1  
        self.save(update_fields=['download_count']) 