from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
      # OneToOneField giúp mỗi User có một Profile.
      user = models.OneToOneField(User, on_delete=models.CASCADE)
      avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
      bio = models.TextField(null=True, blank=True)
      favorite_tracks = models.ManyToManyField('music.Track', blank=True, related_name='favorited_by')
      favorite_artists = models.ManyToManyField('music.Artist', blank=True, related_name='favorited_by')
      favorite_albums = models.ManyToManyField('music.Album', blank=True, related_name='favorited_by')
      created_at = models.DateTimeField(auto_now_add=True)

      def __str__(self):
          return self.user.username
      
      