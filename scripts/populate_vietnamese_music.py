import os
import sys
import django
from django.core.files import File
from datetime import datetime

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from django.contrib.auth.models import User
from artists.models import Artist
from tracks.models import Track
from albums.models import Album
from playlists.models import Playlist

def create_vietnamese_artists():
    artists_data = [
        {
            'name': 'Sơn Tùng M-TP',
            'bio': 'Sơn Tùng M-TP is a Vietnamese singer, songwriter, and actor. He is known for his unique style and successful music career.',
        },
        {
            'name': 'Hòa Minzy',
            'bio': 'Hòa Minzy is a Vietnamese singer known for her powerful voice and emotional ballads.',
        },
        {
            'name': 'Jack',
            'bio': 'Jack is a Vietnamese singer and songwriter known for his emotional songs and unique voice.',
        },
        {
            'name': 'Mono',
            'bio': 'Mono is a Vietnamese rapper and producer known for his unique style and successful career.',
        },
    ]

    artists = []
    for data in artists_data:
        artist, created = Artist.objects.get_or_create(
            name=data['name'],
            defaults={'bio': data['bio']}
        )
        artists.append(artist)
        print(f"{'Created' if created else 'Found'} artist: {artist.name}")

    return artists

def create_vietnamese_tracks(artists):
    tracks_data = [
        {
            'title': 'Âm Thầm Bên Em',
            'artist_name': 'Sơn Tùng M-TP',
            'file_name': 'Âm_Thầm_Bên_Em.mp3',
            'duration': 240,  # 4 minutes
        },
        {
            'title': 'Chăm Hoa',
            'artist_name': 'Hòa Minzy',
            'file_name': 'Chăm_Hoa.mp3',
            'duration': 245,  # 4:05 minutes
        },
        {
            'title': 'Bầu Trời Mới',
            'artist_name': 'Jack',
            'file_name': 'Bầu_Trời_Mới.mp3',
            'duration': 235,  # 3:55 minutes
        },
        {
            'title': 'Bắc Bling Bắc Ninh',
            'artist_name': 'Mono',
            'file_name': 'Bắc_Bling_Bắc_Ninh_Prod._by_Masew.mp3',
            'duration': 250,  # 4:10 minutes
        },
        {
            'title': '1000 Ánh Mắt',
            'artist_name': 'Jack',
            'file_name': '1000_Ánh_Mắt.mp3',
            'duration': 230,  # 3:50 minutes
        },
        {
            'title': 'Chạy Ngay Đi',
            'artist_name': 'Sơn Tùng M-TP',
            'file_name': 'ChayNgayDi-SonTungMTP-5468704.mp3',
            'duration': 245,  # 4:05 minutes
        },
    ]

    tracks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'media', 'tracks')
    created_tracks = []
    
    for data in tracks_data:
        artist = next((a for a in artists if a.name == data['artist_name']), None)
        if not artist:
            print(f"Artist not found: {data['artist_name']}")
            continue

        file_path = os.path.join(tracks_dir, data['file_name'])
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        with open(file_path, 'rb') as f:
            track, created = Track.objects.get_or_create(
                title=data['title'],
                artist=artist,
                defaults={
                    'duration': data['duration'],
                    'is_downloadable': True,
                }
            )
            
            if created:
                track.file.save(data['file_name'], File(f), save=True)
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

    playlists_data = [
        {
            'name': 'Vietnamese Pop Hits',
            'description': 'The best of Vietnamese pop music',
            'is_public': True,
            'tracks': ['Âm Thầm Bên Em', 'Chạy Ngay Đi', '1000 Ánh Mắt'],
        },
        {
            'name': 'Vietnamese Ballads',
            'description': 'Beautiful Vietnamese ballads',
            'is_public': True,
            'tracks': ['Chăm Hoa', 'Bầu Trời Mới'],
        },
        {
            'name': 'Vietnamese Hip Hop',
            'description': 'Best of Vietnamese hip hop',
            'is_public': True,
            'tracks': ['Bắc Bling Bắc Ninh'],
        },
        {
            'name': 'Sơn Tùng M-TP Collection',
            'description': 'Best tracks from Sơn Tùng M-TP',
            'is_public': True,
            'tracks': ['Âm Thầm Bên Em', 'Chạy Ngay Đi'],
        },
        {
            'name': 'Jack Hits',
            'description': 'Popular tracks from Jack',
            'is_public': True,
            'tracks': ['Bầu Trời Mới', '1000 Ánh Mắt'],
        },
    ]

    for data in playlists_data:
        playlist, created = Playlist.objects.get_or_create(
            name=data['name'],
            user=system_user,
            defaults={
                'is_public': data['is_public'],
            }
        )
        
        # Add tracks to playlist
        for track_title in data['tracks']:
            track = next((t for t in tracks if t.title == track_title), None)
            if track:
                playlist.tracks.add(track)
        
        print(f"{'Created' if created else 'Updated'} playlist: {playlist.name} with {playlist.tracks.count()} tracks")

def main():
    print("Creating Vietnamese artists...")
    artists = create_vietnamese_artists()
    
    print("\nCreating Vietnamese tracks...")
    tracks = create_vietnamese_tracks(artists)
    
    print("\nCreating system playlists...")
    create_system_playlists(tracks)
    
    print("\nDone!")

if __name__ == '__main__':
    main() 