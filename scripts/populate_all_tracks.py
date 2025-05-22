import os
import sys
import django
from django.core.files import File

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from django.contrib.auth.models import User
from artists.models import Artist
from tracks.models import Track
from playlists.models import Playlist

def create_artists_from_tracks():
    # Get all MP3 files from the tracks directory
    tracks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'tracks')
    mp3_files = [f for f in os.listdir(tracks_dir) if f.endswith('.mp3')]
    
    # Extract unique artist names from filenames
    artist_names = set()
    for mp3_file in mp3_files:
        # Remove file extension and clean up the name
        name = os.path.splitext(mp3_file)[0]
        # Handle special cases where artist name might be in parentheses or after "feat."
        if "feat." in name:
            main_artist = name.split("feat.")[0].strip()
            artist_names.add(main_artist)
            # Add featured artists
            featured = name.split("feat.")[1].strip()
            if "&" in featured:
                for artist in featured.split("&"):
                    artist_names.add(artist.strip())
            else:
                artist_names.add(featured)
        else:
            artist_names.add(name)

    # Create artists
    artists = []
    for name in artist_names:
        artist, created = Artist.objects.get_or_create(
            name=name,
            defaults={'bio': f'Artist: {name}'}
        )
        artists.append(artist)
        print(f"{'Created' if created else 'Found'} artist: {artist.name}")

    return artists

def create_tracks(artists):
    tracks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'tracks')
    mp3_files = [f for f in os.listdir(tracks_dir) if f.endswith('.mp3')]
    created_tracks = []

    for mp3_file in mp3_files:
        file_path = os.path.join(tracks_dir, mp3_file)
        title = os.path.splitext(mp3_file)[0]

        # Try to find the artist
        artist = None
        if "feat." in title:
            main_artist_name = title.split("feat.")[0].strip()
            artist = next((a for a in artists if a.name == main_artist_name), None)
        else:
            artist = next((a for a in artists if a.name == title), None)

        if not artist:
            print(f"Could not find artist for track: {title}")
            continue

        with open(file_path, 'rb') as f:
            track, created = Track.objects.get_or_create(
                title=title,
                artist=artist,
                defaults={
                    'duration': 240,  # Default duration of 4 minutes
                    'is_downloadable': True,
                }
            )
            
            if created:
                track.file.save(mp3_file, File(f), save=True)
                print(f"Created track: {track.title} by {track.artist.name}")
            else:
                print(f"Track already exists: {track.title} by {track.artist.name}")
            
            created_tracks.append(track)

    return created_tracks

def create_system_playlists(tracks):
    # Get or create system user
    system_user, created = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@spotify.com',
            'is_staff': True,
        }
    )
    if created:
        system_user.set_password('system123')
        system_user.save()

    # Create a playlist for all tracks
    playlist, created = Playlist.objects.get_or_create(
        name='All Vietnamese Tracks',
        user=system_user,
        defaults={
            'is_public': True,
        }
    )
    
    # Add all tracks to the playlist
    for track in tracks:
        playlist.tracks.add(track)
    
    print(f"{'Created' if created else 'Updated'} playlist: {playlist.name} with {playlist.tracks.count()} tracks")

def main():
    print("Creating artists from tracks...")
    artists = create_artists_from_tracks()
    
    print("\nCreating tracks...")
    tracks = create_tracks(artists)
    
    print("\nCreating system playlist...")
    create_system_playlists(tracks)
    
    print("\nDone!")

if __name__ == '__main__':
    main() 