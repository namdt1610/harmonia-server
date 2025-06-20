import os
import sys
import django
from django.core.files import File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from urllib.parse import unquote

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from tracks.models import Track
from artists.models import Artist

def check_tracks():
    print("\n=== Checking all tracks ===")
    tracks = Track.objects.all()
    for track in tracks:
        print(f"Track: {track.title}")
        print(f"Artist ID: {track.artist.id}")
        print(f"Artist Name: {track.artist.name}")
        print(f"File path: {track.file.path if track.file else 'No file'}")
        print("---")

    print("\n=== Checking tracks with artist_id 145 ===")
    tracks_145 = Track.objects.filter(artist_id=145)
    for track in tracks_145:
        print(f"Track: {track.title}")
        print(f"File path: {track.file.path if track.file else 'No file'}")
        print("---")

def clean_filename(filename):
    # Tách tên file thành các phần
    parts = filename.split('_')
    # Tìm phần đầu tiên không phải là số
    for i, part in enumerate(parts):
        if not part.isdigit():
            # Lấy phần còn lại của tên file
            return '_'.join(parts[i:])
    return filename

def fix_track_paths():
    tracks = Track.objects.all()
    updated = 0
    for track in tracks:
        if track.file:
            try:
                # Lấy tên file gốc và decode URL
                old_filename = os.path.basename(track.file.name)
                decoded_filename = unquote(old_filename)
                
                # Xóa các số ID lặp lại
                clean_name = clean_filename(decoded_filename)
                
                # Tạo đường dẫn mới theo format content/audio/original/artist_id/artist_id_filename
                new_path = f"content/audio/original/{track.artist.id}/{track.artist.id}_{clean_name}"
                
                # Update trong database
                track.file.name = new_path
                track.save()
                updated += 1
                print(f"Updated path for {track.title}:")
                print(f"Old path: {track.file.name}")
                print(f"New path: {new_path}")
                print("---")
            except Exception as e:
                print(f"Error updating {track.title}: {e}")
    print(f"\nUpdated {updated} tracks.")

if __name__ == "__main__":
    check_tracks()
    fix_track_paths() 