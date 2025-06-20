import os
import shutil
from django.core.management.base import BaseCommand
from django.core.files import File
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from genres.models import Genre
from django.conf import settings
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, APIC
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import tracks from the tracks folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tracks-dir',
            type=str,
            help='Path to directory containing MP3 files',
            default=None
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reimport even if track exists'
        )

    def extract_metadata(self, file_path):
        """Extract metadata from MP3 file"""
        try:
            audio = MP3(file_path, ID3=ID3)
            tags = audio.tags if audio.tags else {}
            
            metadata = {
                'duration': int(audio.info.length),
                'title': None,
                'artist': None,
                'album': None,
                'genres': [],
                'cover': None
            }
            
            # Extract title
            if 'TIT2' in tags:
                metadata['title'] = str(tags['TIT2'])
            
            # Extract artist
            if 'TPE1' in tags:
                metadata['artist'] = str(tags['TPE1'])
            
            # Extract album
            if 'TALB' in tags:
                metadata['album'] = str(tags['TALB'])
            
            # Extract genres
            if 'TCON' in tags:
                genres = str(tags['TCON']).split('/')
                metadata['genres'] = [g.strip() for g in genres]
            
            # Extract cover art
            for tag in tags.values():
                if isinstance(tag, APIC):
                    metadata['cover'] = tag.data
                    break
            
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            return None

    def extract_artist_name(self, filename, metadata=None):
        """Extract artist name from filename or metadata"""
        if metadata and metadata.get('artist'):
            return metadata['artist']
            
        # Remove file extension
        name = os.path.splitext(filename)[0]
        
        # Handle special cases
        if "feat." in name:
            # Get main artist (before feat.)
            main_artist = name.split("feat.")[0].strip()
            return main_artist
        elif "(" in name:
            # Get main artist (before parentheses)
            main_artist = name.split("(")[0].strip()
            return main_artist
        else:
            return name

    def check_track_exists(self, track_name, file_path):
        """Check if track exists and has valid audio file"""
        try:
            track = Track.objects.get(title=track_name)
            # Check if file exists in media directory
            if track.file and os.path.exists(track.file.path):
                return True
            # If file doesn't exist, delete the track record
            track.delete()
            return False
        except Track.DoesNotExist:
            return False

    def handle(self, *args, **options):
        # Get tracks directory from arguments or use default
        tracks_dir = options['tracks_dir']
        if not tracks_dir:
            tracks_dir = os.path.join(settings.BASE_DIR, '..', 'tracks')
        
        # Check if directory exists
        if not os.path.exists(tracks_dir):
            self.stdout.write(self.style.ERROR(f"Tracks directory not found: {tracks_dir}"))
            self.stdout.write(self.style.WARNING("Please create the directory or specify a different path using --tracks-dir"))
            return
        
        # Get all mp3 files
        try:
            mp3_files = [f for f in os.listdir(tracks_dir) if f.lower().endswith('.mp3')]
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading tracks directory: {e}"))
            return

        if not mp3_files:
            self.stdout.write(self.style.WARNING(f"No MP3 files found in {tracks_dir}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(mp3_files)} MP3 files"))
        
        # Create artists from filenames and metadata
        artist_names = set()
        for mp3_file in mp3_files:
            file_path = os.path.join(tracks_dir, mp3_file)
            metadata = self.extract_metadata(file_path)
            artist_name = self.extract_artist_name(mp3_file, metadata)
            artist_names.add(artist_name)

        # Create artists
        artists = {}
        for name in artist_names:
            artist, created = Artist.objects.get_or_create(
                name=name,
                defaults={
                    "bio": f"Artist: {name}",
                    "image": None
                }
            )
            artists[name] = artist
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Found'} artist: {name}"))

        # Create genres
        genres = {}
        for mp3_file in mp3_files:
            file_path = os.path.join(tracks_dir, mp3_file)
            metadata = self.extract_metadata(file_path)
            if metadata and metadata.get('genres'):
                for genre_name in metadata['genres']:
                    if genre_name not in genres:
                        genre, created = Genre.objects.get_or_create(name=genre_name)
                        genres[genre_name] = genre
                        self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Found'} genre: {genre_name}"))
        
        # Create default genre if none exists
        if not genres:
            default_genre, _ = Genre.objects.get_or_create(name="Unknown")
            genres["Unknown"] = default_genre
        
        # Track import progress
        total_tracks = len(mp3_files)
        imported_tracks = 0
        skipped_tracks = 0
        failed_tracks = 0
        
        for mp3_file in mp3_files:
            try:
                file_path = os.path.join(tracks_dir, mp3_file)
                metadata = self.extract_metadata(file_path)
                
                # Get track name from metadata or filename
                track_name = metadata['title'] if metadata and metadata.get('title') else os.path.splitext(mp3_file)[0]
                
                # Check if track exists and has valid audio file
                if not options['force'] and self.check_track_exists(track_name, file_path):
                    self.stdout.write(f"Track '{track_name}' already exists with valid audio file, skipping...")
                    skipped_tracks += 1
                    continue

                # Get artist for this track
                artist_name = self.extract_artist_name(mp3_file, metadata)
                artist = artists[artist_name]

                # Get or create album
                album_title = metadata['album'] if metadata and metadata.get('album') else "Unknown Album"
                album, _ = Album.objects.get_or_create(
                    title=album_title,
                    artist=artist,
                    defaults={
                        "release_date": "2024-01-01",
                        "image": None
                    }
                )

                # Create track
                track = Track.objects.create(
                    title=track_name,
                    artist=artist,
                    album=album,
                    duration=metadata['duration'] if metadata and metadata.get('duration') else 0,
                    image=None
                )

                # Add genres
                if metadata and metadata.get('genres'):
                    for genre_name in metadata['genres']:
                        if genre_name in genres:
                            track.genres.add(genres[genre_name])
                else:
                    track.genres.add(list(genres.values())[0])

                # Create artist directory in media/content/audio/original
                artist_media_dir = os.path.join(settings.MEDIA_ROOT, 'content', 'audio', 'original', str(artist.id))
                os.makedirs(artist_media_dir, exist_ok=True)

                # Copy file to media directory
                dest_path = os.path.join(artist_media_dir, mp3_file)
                shutil.copy2(file_path, dest_path)

                # Update track file path
                track.file = f'content/audio/original/{artist.id}/{mp3_file}'
                
                # Save cover art if exists
                if metadata and metadata.get('cover'):
                    cover_data = BytesIO(metadata['cover'])
                    track.image.save(
                        f'{track.id}_cover.jpg',
                        File(cover_data),
                        save=False
                    )
                
                track.save()
                imported_tracks += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully imported track '{track_name}'"))

            except Exception as e:
                failed_tracks += 1
                self.stdout.write(self.style.ERROR(f"Failed to import track '{mp3_file}': {e}"))
                continue

        # Print summary
        self.stdout.write("\nImport Summary:")
        self.stdout.write(f"Total tracks found: {total_tracks}")
        self.stdout.write(f"Successfully imported: {imported_tracks}")
        self.stdout.write(f"Skipped (already exist): {skipped_tracks}")
        self.stdout.write(f"Failed to import: {failed_tracks}") 