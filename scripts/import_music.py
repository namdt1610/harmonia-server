import os
import sys
import django
from django.core.files import File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from artists.models import Artist
from albums.models import Album
from tracks.models import Track
from genres.models import Genre

def import_music():
    # Create a default artist
    artist, created = Artist.objects.get_or_create(
        name="Default Artist",
        defaults={
            'bio': "A collection of music tracks"
        }
    )
    print(f"{'Created' if created else 'Found'} artist: {artist.name}")

    # Create a default album
    album, created = Album.objects.get_or_create(
        title="Music Collection",
        artist=artist,
        defaults={
            'description': "A collection of music tracks"
        }
    )
    print(f"{'Created' if created else 'Found'} album: {album.title}")

    # Create a default genre
    genre, created = Genre.objects.get_or_create(
        name="Pop",
        defaults={
            'description': "Popular music"
        }
    )
    print(f"{'Created' if created else 'Found'} genre: {genre.name}")

    # Get all MP3 files from the audio directory
    audio_dir = os.path.join(project_dir, 'media', 'content', 'audio', 'original', '146')
    mp3_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
    
    # Sort files by track number
    mp3_files.sort(key=lambda x: int(x.split('_')[0]))

    # Import each track
    for mp3_file in mp3_files:
        file_path = os.path.join(audio_dir, mp3_file)
        track_number = int(mp3_file.split('_')[0])
        
        # Get audio metadata
        audio = MP3(file_path)
        duration = int(audio.info.length)
        
        # Create track
        track, created = Track.objects.get_or_create(
            title=f"Track {track_number}",
            artist=artist,
            album=album,
            defaults={
                'duration': duration,
                'is_downloadable': True
            }
        )
        
        # Add file if newly created
        if created:
            with open(file_path, 'rb') as f:
                track.file.save(mp3_file, File(f), save=True)
            track.genres.add(genre)
            print(f"Created track: {track.title}")
        else:
            print(f"Found existing track: {track.title}")

if __name__ == '__main__':
    import_music() 