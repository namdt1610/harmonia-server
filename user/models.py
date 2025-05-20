from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
      # OneToOneField giúp mỗi User có một Profile.
      user = models.OneToOneField(User, on_delete=models.CASCADE)
      avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
      bio = models.TextField(null=True, blank=True)
      recently_played = models.ForeignKey('tracks.Track', null=True, blank=True, on_delete=models.SET_NULL, related_name='current_listeners')
      playlists = models.ManyToManyField('playlists.Playlist', blank=True, related_name='users')
      favorite_tracks = models.ManyToManyField('tracks.Track', blank=True, related_name='favorited_by_profiles')
      favorite_artists = models.ManyToManyField('artists.Artist', blank=True, related_name='favorited_by_profiles')
      favorite_albums = models.ManyToManyField('albums.Album', blank=True, related_name='favorited_by_profiles')
      created_at = models.DateTimeField(auto_now_add=True)

      def __str__(self):
          return self.user.username
      
      