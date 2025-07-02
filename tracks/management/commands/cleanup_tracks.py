from django.core.management.base import BaseCommand
from django.db import transaction
from tracks.models import Track
from playlists.models import PlaylistTrack
from favorites.models import Favorite
from user_activity.models import PlayHistory
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Cleanup tracks with missing files and orphaned references'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--delete-orphaned-files',
            action='store_true',
            help='Delete orphaned media files that no longer have track records',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting track cleanup...'))
        
        dry_run = options['dry_run']
        delete_orphaned_files = options['delete_orphaned_files']
        
        # 1. Find tracks with missing files
        tracks_with_missing_files = []
        all_tracks = Track.objects.all()
        
        self.stdout.write(f'Checking {all_tracks.count()} tracks for missing files...')
        
        for track in all_tracks:
            if track.file and not os.path.exists(track.file.path):
                tracks_with_missing_files.append(track)
                
        self.stdout.write(
            self.style.WARNING(f'Found {len(tracks_with_missing_files)} tracks with missing files')
        )
        
        # 2. Show details of tracks to be deleted
        if tracks_with_missing_files:
            self.stdout.write('\nTracks with missing files:')
            for track in tracks_with_missing_files:
                self.stdout.write(f'  - Track {track.id}: "{track.title}" by {track.artist.name}')
                self.stdout.write(f'    Missing file: {track.file.name}')
                
                # Count related objects
                playlist_count = PlaylistTrack.objects.filter(track=track).count()
                favorite_count = Favorite.objects.filter(track=track).count()
                play_history_count = PlayHistory.objects.filter(track=track).count()
                
                self.stdout.write(f'    Related objects: {playlist_count} playlists, {favorite_count} favorites, {play_history_count} play history entries')
        
        # 3. Delete tracks and related objects
        if tracks_with_missing_files and not dry_run:
            self.stdout.write(self.style.WARNING('\nDeleting tracks with missing files...'))
            
            with transaction.atomic():
                for track in tracks_with_missing_files:
                    # Delete related objects first
                    PlaylistTrack.objects.filter(track=track).delete()
                    Favorite.objects.filter(track=track).delete() 
                    PlayHistory.objects.filter(track=track).delete()
                    
                    # Delete the track
                    track.delete()
                    self.stdout.write(f'  Deleted track {track.id}: {track.title}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {len(tracks_with_missing_files)} tracks')
            )
        
        # 4. Find orphaned media files (optional)
        if delete_orphaned_files:
            self.stdout.write('\nChecking for orphaned media files...')
            
            # Get all track file paths from database
            existing_track_files = set()
            for track in Track.objects.all():
                if track.file:
                    existing_track_files.add(os.path.basename(track.file.name))
                if track.image:
                    existing_track_files.add(os.path.basename(track.image.name))
                if track.video:
                    existing_track_files.add(os.path.basename(track.video.name))
                if track.video_thumbnail:
                    existing_track_files.add(os.path.basename(track.video_thumbnail.name))
            
            # Check media directories for orphaned files
            orphaned_files = []
            media_root = settings.MEDIA_ROOT
            
            if os.path.exists(media_root):
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        if file not in existing_track_files and not file.startswith('.'):
                            orphaned_files.append(os.path.join(root, file))
            
            self.stdout.write(f'Found {len(orphaned_files)} orphaned files')
            
            if orphaned_files:
                for file_path in orphaned_files[:10]:  # Show first 10
                    self.stdout.write(f'  - {file_path}')
                if len(orphaned_files) > 10:
                    self.stdout.write(f'  ... and {len(orphaned_files) - 10} more files')
                
                if not dry_run:
                    self.stdout.write(self.style.WARNING('Deleting orphaned files...'))
                    deleted_count = 0
                    for file_path in orphaned_files:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except OSError as e:
                            self.stdout.write(
                                self.style.ERROR(f'Error deleting {file_path}: {e}')
                            )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Deleted {deleted_count} orphaned files')
                    )
        
        # 5. Summary
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nDRY RUN - No changes were made. Use --dry-run=false to apply changes.')
            )
        else:
            self.stdout.write(self.style.SUCCESS('\nCleanup completed!')) 