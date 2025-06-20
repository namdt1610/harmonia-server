from django.core.management.base import BaseCommand
from tracks.models import Track
from django.db.models import F

class Command(BaseCommand):
    help = 'List all tracks in the database with their details'

    def handle(self, *args, **options):
        tracks = Track.objects.all().select_related('artist', 'album').prefetch_related('genres')
        
        if not tracks.exists():
            self.stdout.write(self.style.WARNING('No tracks found in the database.'))
            return

        self.stdout.write(self.style.SUCCESS(f'Found {tracks.count()} tracks:\n'))
        
        for track in tracks:
            # Format duration from seconds to MM:SS
            duration = f"{track.duration // 60}:{track.duration % 60:02d}" if track.duration else "N/A"
            
            # Get genre names
            genre_names = [genre.name for genre in track.genres.all()]
            genres_str = ', '.join(genre_names) if genre_names else 'No genres'
            
            # Format the track information
            track_info = (
                f"ID: {track.id}\n"
                f"Title: {track.title}\n"
                f"Artist: {track.artist.name}\n"
                f"Album: {track.album.title if track.album else 'No album'}\n"
                f"Duration: {duration}\n"
                f"Genres: {genres_str}\n"
                f"Play Count: {track.play_count}\n"
                f"Download Count: {track.download_count}\n"
                f"Created: {track.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"{'=' * 50}"
            )
            
            self.stdout.write(track_info) 