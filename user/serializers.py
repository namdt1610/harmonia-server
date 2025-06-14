from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'user', 'bio',
            'avatar',
            'recently_played',
            'playlists',
            'favorite_tracks',
            'favorite_artists',
            'favorite_albums'
        ]