from django.db import models
from artists.models import Artist
from genres.models import Genre

class Album(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="albums")
    release_date = models.DateField(null=True, blank=True)
    cover_image = models.ImageField(upload_to="album_covers/", blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name="albums", blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["artist"]),
            models.Index(fields=["release_date"]),
        ]
        ordering = ["-release_date", "title"]

    def __str__(self):
        return f"{self.title} - {self.artist.name}" 