from django.db import models
from django.core.exceptions import ValidationError

# Import models from separate apps
from artists.models import Artist
from albums.models import Album 
from genres.models import Genre
from tracks.models import Track, validate_audio_file
from playlists.models import Playlist
from user_activity.models import UserActivity

# Keep this here for backwards compatibility
__all__ = ['Artist', 'Album', 'Genre', 'Track', 'Playlist', 'UserActivity', 'validate_audio_file']