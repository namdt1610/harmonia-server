from django.db import models
from artists.models import Artist

class Album(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="albums")
    release_date = models.DateField(default=None, blank=True, null=True)
    image = models.ImageField(upload_to='albums/images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-release_date"]
        unique_together = ("title", "artist")  # Một artist không có 2 album trùng tên

    def __str__(self):
        return f"{self.title} - {self.artist.name}" 