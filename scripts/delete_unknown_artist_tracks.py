import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spotify.settings')
django.setup()

from tracks.models import Track
from artists.models import Artist

def delete_unknown_artist_tracks():
    print("=== Deleting tracks with Unknown Artist ===")
    
    # Find artist with name 'Unknown Artist'
    unknown_artists = Artist.objects.filter(name__iexact='Unknown Artist')
    
    total_deleted = 0
    
    for unknown in unknown_artists:
        tracks_to_delete = Track.objects.filter(artist=unknown)
        count = tracks_to_delete.count()
        
        if count > 0:
            print(f"Found {count} tracks with artist '{unknown.name}'")
            
            # List tracks before deletion
            for track in tracks_to_delete:
                print(f"  - {track.title}")
            
            # Delete tracks
            deleted, details = tracks_to_delete.delete()
            total_deleted += deleted
            print(f"Deleted {deleted} tracks with artist '{unknown.name}'")
        else:
            print(f"No tracks found with artist '{unknown.name}'")
    
    # Also delete tracks with no artist (artist=None)
    orphan_tracks = Track.objects.filter(artist=None)
    orphan_count = orphan_tracks.count()
    
    if orphan_count > 0:
        print(f"\nFound {orphan_count} tracks with no artist:")
        for track in orphan_tracks:
            print(f"  - {track.title}")
        
        deleted, details = orphan_tracks.delete()
        total_deleted += deleted
        print(f"Deleted {deleted} orphan tracks")
    
    print(f"\n=== Total deleted: {total_deleted} tracks ===")
    
    # Show remaining tracks count
    remaining_tracks = Track.objects.count()
    print(f"Remaining tracks in database: {remaining_tracks}")

if __name__ == '__main__':
    delete_unknown_artist_tracks() 