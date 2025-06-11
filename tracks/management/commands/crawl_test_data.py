import os
import requests
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from genres.models import Genre
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, APIC
from io import BytesIO
import random
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Crawl test media data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of tracks to download'
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(f'Starting to crawl {count} test tracks...')

        # Create test artist if not exists
        artist, _ = Artist.objects.get_or_create(
            name="Test Artist",
            defaults={
                'bio': "A test artist for development",
                'image': None
            }
        )

        # Create test album if not exists
        album, _ = Album.objects.get_or_create(
            title="Test Album",
            artist=artist,
            defaults={
                'release_date': '2024-01-01',
                'cover': None
            }
        )

        # Create test genre if not exists
        genre, _ = Genre.objects.get_or_create(
            name="Test Genre",
            defaults={
                'description': "A test genre for development"
            }
        )

        # Sample MP3 URLs (free music)
        sample_tracks = [
            {
                'title': 'Sample Track 1',
                'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
                'duration': 180
            },
            {
                'title': 'Sample Track 2',
                'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
                'duration': 240
            },
            {
                'title': 'Sample Track 3',
                'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
                'duration': 200
            }
        ]

        # Sample thumbnail URLs
        sample_thumbnails = [
            'https://picsum.photos/300/300',
            'https://picsum.photos/300/300',
            'https://picsum.photos/300/300'
        ]

        for i in range(count):
            try:
                # Select random track data
                track_data = random.choice(sample_tracks)
                thumbnail_url = random.choice(sample_thumbnails)

                # Download track
                self.stdout.write(f'Downloading track {i+1}/{count}: {track_data["title"]}')
                track_response = requests.get(track_data['url'])
                track_response.raise_for_status()

                # Download thumbnail
                thumbnail_response = requests.get(thumbnail_url)
                thumbnail_response.raise_for_status()

                # Create track
                track = Track.objects.create(
                    title=f"{track_data['title']} {i+1}",
                    artist=artist,
                    album=album,
                    duration=track_data['duration'],
                    is_downloadable=True
                )
                track.genres.add(genre)

                # Save track file
                track.file.save(
                    f'track_{i+1}.mp3',
                    BytesIO(track_response.content),
                    save=True
                )

                # Save thumbnail
                track.track_thumbnail.save(
                    f'thumbnail_{i+1}.jpg',
                    BytesIO(thumbnail_response.content),
                    save=True
                )

                # Add ID3 tags
                audio = MP3(track.file.path, ID3=ID3)
                audio.tags.add(TIT2(encoding=3, text=track.title))
                audio.tags.add(TPE1(encoding=3, text=artist.name))
                audio.tags.add(TALB(encoding=3, text=album.title))
                audio.tags.add(TCON(encoding=3, text=genre.name))
                
                # Add thumbnail as cover art
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=thumbnail_response.content
                ))
                audio.save()

                self.stdout.write(self.style.SUCCESS(f'Successfully created track: {track.title}'))
                
                # Sleep to avoid rate limiting
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error creating track {i+1}: {str(e)}")
                self.stdout.write(self.style.ERROR(f'Error creating track {i+1}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} test tracks')) 