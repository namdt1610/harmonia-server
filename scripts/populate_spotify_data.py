#!/usr/bin/env python
import os
import sys
import django
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import time
import random
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files import File

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

# Import models after Django is set up
from artists.models import Artist
from albums.models import Album
from tracks.models import Track
from genres.models import Genre
from django.contrib.auth.models import User
from playlists.models import Playlist

# Import Spotify API credentials from config
try:
    from scripts.spotify_config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
except ImportError:
    print("Error: Could not import Spotify credentials.")
    print("Please create scripts/spotify_config.py with your Spotify API credentials.")
    print("See scripts/spotify_config.py.example for the format.")
    sys.exit(1)

# Set up Spotify client
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))
except:
    print("Error: Could not authenticate with Spotify API.")
    print("Please check your credentials in scripts/spotify_config.py")
    sys.exit(1)

def download_image(url):
    """Download image from URL and return as ContentFile"""
    if not url:
        return None
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return ContentFile(response.content, name=url.split('/')[-1])
        return None
    except:
        return None

def get_or_create_genre(name):
    """Get or create a genre by name"""
    genre, created = Genre.objects.get_or_create(
        name=name,
        defaults={'description': f'Music in the {name} genre'}
    )
    return genre

def populate_artists(artist_names, limit=10):
    """Fetch and create artists"""
    artists_created = []
    
    for name in artist_names[:limit]:
        results = sp.search(q=f'artist:{name}', type='artist', limit=1)
        
        if results['artists']['items']:
            artist_data = results['artists']['items'][0]
            
            # Create artist
            artist, created = Artist.objects.get_or_create(
                name=artist_data['name'],
                defaults={
                    'bio': f"Bio for {artist_data['name']}"
                }
            )
            
            # Add profile image if available
            if artist_data['images'] and len(artist_data['images']) > 0:
                image_url = artist_data['images'][0]['url']
                image_content = download_image(image_url)
                if image_content:
                    artist.avatar.save(f"{artist.name.replace(' ', '_')}.jpg", image_content, save=True)
            
            artists_created.append(artist)
            print(f"Added artist: {artist.name}")
            
            # Avoid rate limiting
            time.sleep(0.5)
    
    return artists_created

def populate_albums(artists, albums_per_artist=2):
    """Fetch and create albums for artists"""
    albums_created = []
    
    for artist in artists:
        results = sp.search(q=f'artist:{artist.name} album', type='album', limit=albums_per_artist)
        
        for album_data in results['albums']['items']:
            # Create album
            album, created = Album.objects.get_or_create(
                title=album_data['name'],
                artist=artist,
                defaults={
                    'release_date': album_data.get('release_date', None)
                }
            )
            
            # Add album cover if available
            if album_data['images'] and len(album_data['images']) > 0:
                image_url = album_data['images'][0]['url']
                image_content = download_image(image_url)
                if image_content:
                    album.cover.save(f"{album.title.replace(' ', '_')}.jpg", image_content, save=True)
            
            albums_created.append(album)
            print(f"Added album: {album.title} by {artist.name}")
            
            # Avoid rate limiting
            time.sleep(0.5)
    
    return albums_created

def populate_tracks(albums, tracks_per_album=5):
    """Fetch and create tracks for albums"""
    tracks_created = []
    
    for album in albums:
        artist = album.artist
        
        # Search for tracks by this artist from this album
        results = sp.search(
            q=f'artist:{artist.name} album:{album.title}',
            type='track',
            limit=tracks_per_album
        )
        
        for track_data in results['tracks']['items']:
            # Create track
            track, created = Track.objects.get_or_create(
                title=track_data['name'],
                artist=artist,
                defaults={
                    'album': album,
                    'duration': track_data['duration_ms'] // 1000,  # Convert to seconds
                }
            )
            
            # Create a dummy file for the track since we can't access the actual audio
            # This is a placeholder - in production you'd need real audio files
            if created:
                dummy_file = ContentFile(b"This is a placeholder for audio content", name=f"{track.title.replace(' ', '_')}.mp3")
                track.file.save(f"{track.title.replace(' ', '_')}.mp3", dummy_file, save=True)
            
            tracks_created.append(track)
            print(f"Added track: {track.title}")
            
            # Avoid rate limiting
            time.sleep(0.5)
    
    return tracks_created

def create_sample_playlists(tracks, num_playlists=3):
    """Create sample playlists with tracks"""
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    if created:
        user.set_password('testpassword123')
        user.save()
    
    playlists_created = []
    
    playlist_names = [
        "Top Hits", "Chill Vibes", "Workout Mix", 
        "Road Trip Playlist", "Study Session", "Party Time"
    ]
    
    for i in range(min(num_playlists, len(playlist_names))):
        name = playlist_names[i]
        playlist, created = Playlist.objects.get_or_create(
            name=name,
            user=user,
            defaults={
                'is_public': True
            }
        )
        
        # Add random tracks to playlist (between 5-15 tracks)
        num_tracks = random.randint(5, min(15, len(tracks)))
        selected_tracks = random.sample(list(tracks), num_tracks)
        
        for track in selected_tracks:
            playlist.tracks.add(track)
        
        playlists_created.append(playlist)
        print(f"Created playlist: {playlist.name} with {num_tracks} tracks")
    
    return playlists_created

def main():
    print("Starting to populate database with Spotify data...")
    
    # List of popular artists to fetch
    artist_names = [
        "Taylor Swift", "Ed Sheeran", "Billie Eilish", "Drake", "Ariana Grande",
        "The Weeknd", "BTS", "Dua Lipa", "Justin Bieber", "Bad Bunny",
        "Harry Styles", "Coldplay", "Adele", "Beyoncé", "Post Malone"
    ]
    
    # Populate database
    artists = populate_artists(artist_names, limit=5)
    albums = populate_albums(artists, albums_per_artist=2)
    tracks = populate_tracks(albums, tracks_per_album=5)
    playlists = create_sample_playlists(tracks, num_playlists=3)
    
    print("\nPopulation complete!")
    print(f"Created {len(artists)} artists")
    print(f"Created {len(albums)} albums")
    print(f"Created {len(tracks)} tracks")
    print(f"Created {len(playlists)} playlists")

if __name__ == "__main__":
    main() 