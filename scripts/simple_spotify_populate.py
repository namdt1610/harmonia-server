#!/usr/bin/env python
import os
import sys
import django
import requests
import base64
import time
import random
from django.core.files.base import ContentFile

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

# Spotify API base URL
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1/"

def get_spotify_token():
    """Get an OAuth token for the Spotify API"""
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(auth_url, headers=headers, data=data)
    if response.status_code != 200:
        print(f"Error getting Spotify token: {response.status_code} {response.text}")
        sys.exit(1)
    
    token_data = response.json()
    return token_data["access_token"]

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

def search_spotify(token, query, search_type, limit=10):
    """Search Spotify API"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": query,
        "type": search_type,
        "limit": limit
    }
    
    url = f"{SPOTIFY_API_BASE_URL}search"
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error searching Spotify: {response.status_code} {response.text}")
        return {}
    
    return response.json()

def get_artist_albums(token, artist_id, limit=5):
    """Get albums for an artist"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit}
    
    url = f"{SPOTIFY_API_BASE_URL}artists/{artist_id}/albums"
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error getting artist albums: {response.status_code} {response.text}")
        return {}
    
    return response.json()

def get_album_tracks(token, album_id, limit=10):
    """Get tracks for an album"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit}
    
    url = f"{SPOTIFY_API_BASE_URL}albums/{album_id}/tracks"
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error getting album tracks: {response.status_code} {response.text}")
        return {}
    
    return response.json()

def populate_artists(token, artist_names, limit=5):
    """Fetch and create artists"""
    artists_created = []
    
    for name in artist_names[:limit]:
        results = search_spotify(token, f'artist:{name}', 'artist', 1)
        
        if results and 'artists' in results and results['artists']['items']:
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
            
            artists_created.append((artist, artist_data['id']))
            print(f"Added artist: {artist.name}")
            
            # Avoid rate limiting
            time.sleep(0.5)
    
    return artists_created

def populate_albums(token, artist_tuples, albums_per_artist=2):
    """Fetch and create albums for artists"""
    albums_created = []
    
    for artist_tuple in artist_tuples:
        artist, spotify_id = artist_tuple
        results = get_artist_albums(token, spotify_id, albums_per_artist)
        
        if results and 'items' in results:
            for album_data in results['items']:
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
                
                albums_created.append((album, album_data['id']))
                print(f"Added album: {album.title} by {artist.name}")
                
                # Avoid rate limiting
                time.sleep(0.5)
    
    return albums_created

def populate_tracks(token, album_tuples, tracks_per_album=5):
    """Fetch and create tracks for albums"""
    tracks_created = []
    
    for album_tuple in album_tuples:
        album, spotify_id = album_tuple
        artist = album.artist
        
        results = get_album_tracks(token, spotify_id, tracks_per_album)
        
        if results and 'items' in results:
            for track_data in results['items']:
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
        if tracks:
            num_tracks = random.randint(5, min(15, len(tracks)))
            selected_tracks = random.sample(list(tracks), num_tracks)
            
            for track in selected_tracks:
                playlist.tracks.add(track)
        
            playlists_created.append(playlist)
            print(f"Created playlist: {playlist.name} with {num_tracks} tracks")
    
    return playlists_created

def main():
    print("Starting to populate database with Spotify data...")
    
    # Get Spotify API token
    token = get_spotify_token()
    print("Successfully obtained Spotify API token")
    
    # List of popular artists to fetch
    artist_names = [
        "Taylor Swift", "Ed Sheeran", "Billie Eilish", "Drake", "Ariana Grande",
        "The Weeknd", "BTS", "Dua Lipa", "Justin Bieber", "Bad Bunny",
        "Harry Styles", "Coldplay", "Adele", "Beyoncé", "Post Malone"
    ]
    
    # Populate database
    artists = populate_artists(token, artist_names, limit=5)
    albums = populate_albums(token, artists, albums_per_artist=2)
    tracks = populate_tracks(token, albums, tracks_per_album=5)
    playlists = create_sample_playlists(tracks, num_playlists=3)
    
    print("\nPopulation complete!")
    print(f"Created {len(artists)} artists")
    print(f"Created {len(albums)} albums")
    print(f"Created {len(tracks)} tracks")
    print(f"Created {len(playlists)} playlists")

if __name__ == "__main__":
    main() 