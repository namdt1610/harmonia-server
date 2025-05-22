import os
import sys
import django
from mutagen.mp3 import MP3

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from django.core.files import File

TRACKS_DIR = os.path.join(project_dir, 'media', 'tracks')

# Lấy danh sách nghệ sĩ hiện có
artist_objs = {a.name.lower(): a for a in Artist.objects.all()}
unknown_artist, _ = Artist.objects.get_or_create(name='Unknown Artist', defaults={'bio': 'Unknown'})

def guess_artist_from_filename(filename):
    # Tách tên nghệ sĩ nếu có trong tên file (ví dụ: "Tên_Bài_Hát_feat._Nghệ_Sĩ.mp3")
    name = os.path.splitext(filename)[0]
    for artist_name in artist_objs:
        if artist_name.replace(' ', '_') in name.lower() or artist_name in name.lower():
            return artist_objs[artist_name]
    return unknown_artist

def import_tracks():
    files = [f for f in os.listdir(TRACKS_DIR) if f.endswith('.mp3')]
    print(f"Found {len(files)} mp3 files.")
    added = 0
    for f in files:
        title = os.path.splitext(f)[0].replace('_', ' ')
        file_path = os.path.join('tracks', f)
        # Check duplicate by file or title
        if Track.objects.filter(title=title).exists() or Track.objects.filter(file=file_path).exists():
            print(f"Track already exists: {title}")
            continue
        artist = guess_artist_from_filename(f)
        # Get duration
        try:
            audio = MP3(os.path.join(TRACKS_DIR, f))
            duration = int(audio.info.length)
        except Exception:
            duration = None
        track = Track.objects.create(
            title=title,
            artist=artist,
            file=file_path,
            duration=duration,
        )
        print(f"Added track: {title} - {artist.name}")
        added += 1
    print(f"Done! Imported {added} new tracks.")

if __name__ == "__main__":
    import_tracks() 