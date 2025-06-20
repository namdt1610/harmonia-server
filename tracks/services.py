import logging
from user_activity.models import UserActivity, PlayHistory
from .models import Track
from django.db.models import F
from django.conf import settings
from django.http import Http404, HttpResponse
import os
import re
import mimetypes
import urllib.parse

logger = logging.getLogger(__name__)

class TrackService:
    def __init__(self, user=None):
        self.user = user

    def retrieve_tracks_by_criteria(self, filters):
        queryset = Track.objects.all()
        filter_dict = {
            'genres__name__icontains': filters.get('genre'),
            'artist__name__icontains': filters.get('artist'),
            'album__title__icontains': filters.get('album'),
            'title__icontains': filters.get('search'),
        }
        filter_dict = {k: v for k, v in filter_dict.items() if v}
        return queryset.filter(**filter_dict)

    def retrieve_top_performing_tracks(self, limit=10):
        return Track.objects.annotate(
            total_plays=F('play_count') + F('download_count')
        ).order_by('-total_plays')[:limit]

    def retrieve_currently_playing_track(self):
        if not self.user or not self.user.is_authenticated:
            return Track.objects.order_by('-play_count').first()

        recent_activity = UserActivity.objects.filter(
            user=self.user,
            action='play'
        ).order_by('-timestamp').first()

        if not recent_activity or not recent_activity.track:
            return Track.objects.order_by('-play_count').first()

        return recent_activity.track

    def record_track_play_event(self, track):
        if self.user and self.user.is_authenticated:
            UserActivity.objects.create(
                user=self.user,
                track=track,
                action='play'
            )
            PlayHistory.objects.create(
                user=self.user,
                track=track
            )
            track.increment_play_count()

    def record_track_download_event(self, track):
        if self.user and self.user.is_authenticated:
            UserActivity.objects.create(
                user=self.user,
                track=track,
                action='download'
            )
            track.increment_download_count()

    def retrieve_trending_tracks(self, limit=10):
        return Track.objects.order_by('-play_count')[:limit]

    def retrieve_recently_added_tracks(self, limit=10):
        return Track.objects.order_by('-created_at')[:limit]

    def retrieve_tracks_by_genre_id(self, genre_id):
        return Track.objects.filter(genres__id=genre_id)

class TrackFileService:
    @staticmethod
    def resolve_track_file_path(track):
        possible_paths = []
        
        # 1. Standard path
        standard_path = os.path.join(settings.MEDIA_ROOT, track.file.name.lstrip('/'))
        possible_paths.append(standard_path)
        
        # 2. Path with URL decode
        decoded_name = urllib.parse.unquote(track.file.name)
        decoded_path = os.path.join(settings.MEDIA_ROOT, decoded_name.lstrip('/'))
        possible_paths.append(decoded_path)
        
        # 3. Try with simple file name (no directory)
        simple_name = os.path.basename(track.file.name)
        simple_path = os.path.join(settings.MEDIA_ROOT, 'content', 'audio', 'original', str(track.artist.id), simple_name)
        possible_paths.append(simple_path)
        
        # 4. Simple name decoded
        decoded_simple = urllib.parse.unquote(simple_name)
        decoded_simple_path = os.path.join(settings.MEDIA_ROOT, 'content', 'audio', 'original', str(track.artist.id), decoded_simple)
        possible_paths.append(decoded_simple_path)
        
        # 5. Try with track ID prefix
        id_prefixed_name = f"{track.id}_{os.path.basename(track.file.name)}"
        id_prefixed_path = os.path.join(settings.MEDIA_ROOT, 'content', 'audio', 'original', str(track.artist.id), id_prefixed_name)
        possible_paths.append(id_prefixed_path)
        
        # 6. Try with track ID prefix and decoded name
        id_prefixed_decoded = f"{track.id}_{urllib.parse.unquote(os.path.basename(track.file.name))}"
        id_prefixed_decoded_path = os.path.join(settings.MEDIA_ROOT, 'content', 'audio', 'original', str(track.artist.id), id_prefixed_decoded)
        possible_paths.append(id_prefixed_decoded_path)
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found track file at: {path}")
                return path
                
        logger.error(f"Track file not found. Tried paths: {possible_paths}")
        return None

    @staticmethod
    def determine_file_content_type(file_path):
        content_type, encoding = mimetypes.guess_type(file_path)
        return content_type or 'audio/mpeg'

    @staticmethod
    def process_range_request(file_path, range_header):
        file_size = os.path.getsize(file_path)
        
        if not range_header:
            return None, file_size
            
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not range_match:
            return None, file_size
            
        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        end = min(end, file_size - 1)
        
        return (start, end), file_size

    """
    Tạo ra một HTTP response cho yêu cầu range request (yêu cầu một phần của file).
    """
    @staticmethod
    def create_partial_content_response(file_path, start, end, file_size, content_type):
        with open(file_path, 'rb') as f:
            f.seek(start)
            data = f.read(end - start + 1)
        response = HttpResponse(data, status=206, content_type=content_type)
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Content-Length'] = str(end - start + 1)
        response['Accept-Ranges'] = 'bytes'
        return response

    @staticmethod
    def stream_media_file(request, path):
        """
        Stream a media file with range request support.
        
        Args:
            request: The HTTP request object
            path: The path to the media file relative to MEDIA_ROOT
            
        Returns:
            HttpResponse: The streaming response
            
        Raises:
            Http404: If the file is not found
        """
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.exists(file_path):
            logger.error(f"Media file not found: {file_path}")
            raise Http404(f"Media file not found: {path}")

        range_header = request.META.get('HTTP_RANGE', '').strip()
        if not range_header:
            return TrackFileService.create_file_download_response(file_path, TrackFileService.determine_file_content_type(file_path))

        size = os.path.getsize(file_path)
        byte1, byte2 = 0, None

        m = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if m:
            g = m.groups()
            byte1 = int(g[0])
            if g[1]:
                byte2 = int(g[1])

        length = size - byte1
        if byte2 is not None:
            length = byte2 - byte1 + 1

        return TrackFileService.create_partial_content_response(
            file_path,
            byte1,
            byte1 + length - 1,
            size,
            TrackFileService.determine_file_content_type(file_path)
        )
