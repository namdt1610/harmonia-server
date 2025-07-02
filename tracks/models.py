from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from mutagen.id3 import ID3, APIC
from artists.models import Artist
from albums.models import Album
from genres.models import Genre
from django.db import models
from mutagen.mp3 import MP3
import os

def validate_audio_file(file):
    """Validate audio file size (max 50MB)"""
    max_size = 50 * 1024 * 1024  # 50MB
    if file.size > max_size:
        raise ValidationError("File must be less than 50MB.")

def get_audio_upload_path(instance, filename):
    """Get upload path for audio files"""
    return os.path.join(
        settings.MEDIA_STORAGE['CONTENT']['AUDIO']['ORIGINAL'],
        f"{instance.artist.id}/{instance.id}_{filename}"
    )

def get_video_upload_path(instance, filename):
    """Get upload path for video files"""
    return os.path.join(
        settings.MEDIA_STORAGE['CONTENT']['VIDEO']['ORIGINAL'],
        f"{instance.artist.id}/{instance.id}_{filename}"
    )

def get_track_image_path(instance, filename):
    """Get upload path for track images"""
    return os.path.join(
        settings.MEDIA_STORAGE['CONTENT']['IMAGE']['ORIGINAL'],
        f"{instance.artist.id}/{instance.id}_{filename}"
    )

def get_video_thumbnail_path(instance, filename):
    """Get upload path for video thumbnails"""
    return os.path.join(
        settings.MEDIA_STORAGE['CONTENT']['IMAGE']['THUMBNAIL'],
        f"{instance.artist.id}/{instance.id}_{filename}"
    )

class Track(models.Model):
    # Core fields
    title = models.CharField(max_length=255, db_index=True)
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True, related_name="tracks")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="tracks")
    
    # Media fields
    file = models.FileField(
        upload_to=get_audio_upload_path,
        validators=[validate_audio_file],
        max_length=500
    )
    video = models.FileField(
        upload_to=get_video_upload_path,
        null=True,
        blank=True
    )
    image = models.ImageField(
        upload_to=get_track_image_path,
        blank=True,
        null=True
    )
    video_thumbnail = models.ImageField(
        upload_to=get_video_thumbnail_path,
        blank=True,
        null=True
    )
    
    # Metadata fields
    duration = models.PositiveIntegerField(help_text="Duration in seconds", null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name="tracks", blank=True)
    lyrics = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics fields
    play_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    is_downloadable = models.BooleanField(default=True)
    
    # Meta giúp index và sắp xếp để tăng hiệu suất truy vấn
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
        # Extract cover art if no image exists
        if self.file and not self.image:
            try:
                audio = MP3(self.file.path, ID3=ID3)
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):  # APIC = Attached Picture
                        image_data = tag.data
                        self.image.save(
                            f"{self.id}_cover.jpg",
                            ContentFile(image_data),
                            save=True
                        )
                        break
            except Exception as e:
                print(f"Could not extract cover from audio file: {e}")

    def __str__(self):
        return f"{self.title} - {self.artist.name}"
    
    def increment_play_count(self):
        self.play_count += 1
        self.save(update_fields=['play_count'])
    
    def increment_download_count(self):
        self.download_count += 1  
        self.save(update_fields=['download_count']) 