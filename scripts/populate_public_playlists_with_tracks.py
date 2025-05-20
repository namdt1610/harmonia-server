import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from playlists.models import Playlist
from tracks.models import Track


def add_tracks_to_public_playlists(num_tracks=5):
    public_playlists = Playlist.objects.filter(is_public=True)
    all_tracks = list(Track.objects.all())
    if not all_tracks:
        print('No tracks found in the database.')
        return

    for playlist in public_playlists:
        # Avoid adding duplicate tracks
        current_track_ids = set(playlist.tracks.values_list('id', flat=True))
        available_tracks = [t for t in all_tracks if t.id not in current_track_ids]
        if len(available_tracks) < num_tracks:
            print(f'Not enough unique tracks to add to playlist {playlist.name}')
            continue
        selected_tracks = random.sample(available_tracks, num_tracks)
        for track in selected_tracks:
            playlist.tracks.add(track)
        print(f'Added {num_tracks} tracks to playlist: {playlist.name}')

if __name__ == '__main__':
    add_tracks_to_public_playlists(num_tracks=5) 