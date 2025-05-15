from django.db import models

class Artist(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    bio = models.TextField(blank=True, null=True, default='No bio available')
    avatar = models.ImageField(upload_to='artists/', blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name 