import os
import sys
import django
import random

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from tracks.models import Track
from playlists.models import Playlist

# Nếu Playlist có trường is_public thì lọc, không thì lấy tất cả
try:
    playlists = Playlist.objects.filter(is_public=True)
except Exception:
    playlists = Playlist.objects.all()

all_track_ids = list(Track.objects.values_list('id', flat=True))

for playlist in playlists:
    # Lấy các track chưa có trong playlist
    existing_ids = set(playlist.tracks.values_list('id', flat=True))
    available_ids = list(set(all_track_ids) - existing_ids)
    if not available_ids:
        print(f"Playlist '{playlist.name}' đã có đủ track hoặc không còn track mới để thêm.")
        continue
    # Random 10 track
    to_add = random.sample(available_ids, min(10, len(available_ids)))
    playlist.tracks.add(*to_add)
    print(f"Đã thêm {len(to_add)} track vào playlist '{playlist.name}'")

print("Done!") 