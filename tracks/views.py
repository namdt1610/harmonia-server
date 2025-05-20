from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F
from django.http import HttpResponse, FileResponse, Http404
from django.conf import settings
import os
import re
import mimetypes
import urllib.parse
from .models import Track
from user_activity.models import UserActivity, PlayHistory
from .serializers import TrackSerializer

class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Track.objects.all()
        genre = self.request.query_params.get('genre', None)
        artist = self.request.query_params.get('artist', None)
        album = self.request.query_params.get('album', None)
        search = self.request.query_params.get('search', None)
        
        if genre:
            queryset = queryset.filter(genres__name__icontains=genre)
        if artist:
            queryset = queryset.filter(artist__name__icontains=artist)
        if album:
            queryset = queryset.filter(album__title__icontains=album)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset.distinct()
    
    @action(detail=True, methods=['post'])
    def increment_play_count(self, request, pk=None):
        track = self.get_object()
        track.increment_play_count()
        
        # Record play activity if user is authenticated
        if request.user and request.user.is_authenticated:
            # Create UserActivity record
            UserActivity.objects.create(
                user=request.user,
                track=track,
                action='play'
            )
            
            # Create PlayHistory record for analytics
            PlayHistory.objects.create(
                user=request.user,
                track=track
            )
            
        return Response({'status': 'play count incremented'})
    
    @action(detail=True, methods=['post'])
    def increment_download_count(self, request, pk=None):
        track = self.get_object()
        track.increment_download_count()
        
        # Record download activity if user is authenticated
        if request.user and request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                track=track,
                action='download'
            )
            
        return Response({'status': 'download count incremented'})
    
    @action(detail=False, methods=['get'])
    def top_tracks(self, request):
        top_tracks = Track.objects.annotate(
            total_plays=F('play_count') + F('download_count')
        ).order_by('-total_plays')[:10]
        serializer = self.get_serializer(top_tracks, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'], url_path='current-track', permission_classes=[permissions.AllowAny])
    def current_track(self, request):
        """Get the currently playing track for the authenticated user"""
        
        # First, try to get the user from the authentication mechanism
        user = request.user
        
        # Check if user is authenticated or AnonymousUser
        if not user or not user.is_authenticated:
            # For anonymous users, return the most recent track from cache or database
            most_popular_track = Track.objects.order_by('-play_count').first()
            if most_popular_track:
                serializer = TrackSerializer(most_popular_track)
                return Response(serializer.data)
            else:
                return Response({'error': 'No tracks available'}, 
                              status=status.HTTP_404_NOT_FOUND)
        
        # For authenticated users, get their most recent play activity
        recent_activity = UserActivity.objects.filter(
            user=user,
            action='play'
        ).order_by('-timestamp').first()
        
        if not recent_activity or not recent_activity.track:
            # If authenticated but no recent activity, fall back to popular track
            most_popular_track = Track.objects.order_by('-play_count').first()
            if most_popular_track:
                serializer = TrackSerializer(most_popular_track)
                return Response(serializer.data)
            else:
                return Response({'error': 'No track is currently playing'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # Increment play count for the track
        recent_activity.track.increment_play_count()
        
        # Return the track details
        serializer = TrackSerializer(recent_activity.track)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def play(self, request, pk=None):
        track = self.get_object()
        UserActivity.objects.create(
            user=request.user,
            track=track,
            action='play'
        )
        return Response({'status': 'play recorded'}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        try:
            track = self.get_object()
            
            # Get the track path
            file_path = self._find_track_file_path(track)
            
            if not file_path:
                return self._handle_file_not_found(track)
                
            # Stream the file with proper range support
            return self._stream_file_with_range_support(request, file_path, track)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def _find_track_file_path(self, track):
        """Find the actual path to the track file"""
        # Try multiple ways to find the file
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
        simple_path = os.path.join(settings.MEDIA_ROOT, 'tracks', simple_name)
        possible_paths.append(simple_path)
        
        # 4. Simple name decoded
        decoded_simple = urllib.parse.unquote(simple_name)
        decoded_simple_path = os.path.join(settings.MEDIA_ROOT, 'tracks', decoded_simple)
        possible_paths.append(decoded_simple_path)
        
        # Find the first path that exists
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Found track file at: {path}")
                return path
                
        return None
        
    def _handle_file_not_found(self, track):
        """Handle case when track file is not found"""
        # List all files in tracks directory for debugging
        tracks_dir = os.path.join(settings.MEDIA_ROOT, 'tracks')
        if os.path.exists(tracks_dir):
            track_files = os.listdir(tracks_dir)
            print("Files in tracks directory:")
            for file in track_files:
                print(f"- {file}")
        else:
            print(f"Tracks directory does not exist: {tracks_dir}")
            
        return Response({
            "error": "File not found", 
            "file_name": track.file.name,
        }, status=status.HTTP_404_NOT_FOUND)
        
    def _stream_file_with_range_support(self, request, file_path, track):
        """Stream file with proper HTTP Range support"""
        # Get the file size
        file_size = os.path.getsize(file_path)
        
        # Set content type based on file extension
        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = 'audio/mpeg'  # Default to MP3
            
        # Check for range header
        if 'HTTP_RANGE' in request.META:
            print(f"Range header found: {request.META['HTTP_RANGE']}")
            range_header = request.META['HTTP_RANGE']
            range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            
            if range_match:
                start = int(range_match.group(1))
                end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
                
                # Make sure end is not beyond file size
                end = min(end, file_size - 1)
                length = end - start + 1
                
                print(f"Serving range: {start}-{end}/{file_size}")
                
                # Open file and seek to start position
                file = open(file_path, 'rb')
                file.seek(start)
                
                # Create a proper response with partial content
                response = HttpResponse(
                    file.read(length),
                    status=206,
                    content_type=content_type
                )
                
                # Set required headers for range requests
                response['Content-Length'] = str(length)
                response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
                response['Accept-Ranges'] = 'bytes'
                
                # Record play activity if at the beginning
                if start == 0 and hasattr(request, 'user') and request.user and request.user.is_authenticated:
                    UserActivity.objects.create(
                        user=request.user,
                        track=track,
                        action='play'
                    )
                    
                return response
        
        # If no range header or invalid range, return entire file
        # Use FileResponse for better performance with large files
        print("Serving entire file")
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type
        )
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        
        # Record play activity if full file requested
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                track=track,
                action='play'
            )
            
        return response
        
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        track = self.get_object()
        
        if not track.is_downloadable:
            return Response({'error': 'This track is not available for download'}, 
                         status=status.HTTP_403_FORBIDDEN)
        
        track.increment_download_count()
        
        if request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                track=track,
                action='download'
            )
        
        # Try to get the actual file path
        file_path = self._find_track_file_path(track)
        
        if not file_path:
            return self._handle_file_not_found(track)
            
        # Get just the filename without the path
        filename = os.path.basename(file_path)
        
        # Create a direct download response with the file
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='audio/mpeg',
            as_attachment=True,
            filename=filename
        )
        
        return response
    
    @action(detail=True, methods=['get'])
    def video(self, request, pk=None):
        track = self.get_object()
        
        if not track.music_video:
            return Response({'error': 'No video available for this track'}, 
                         status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'video_url': request.build_absolute_uri(track.music_video.url),
            'thumbnail': request.build_absolute_uri(track.video_thumbnail.url) if track.video_thumbnail else None
        })
    
    @action(detail=False)
    def trending(self, request):
        """Get tracks with the highest play count"""
        tracks = Track.objects.order_by('-play_count')[:10]
        serializer = self.get_serializer(tracks, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def recent(self, request):
        """Get recently added tracks"""
        tracks = Track.objects.order_by('-created_at')[:10]
        serializer = self.get_serializer(tracks, many=True)
        return Response(serializer.data)
    
    @action(detail=False)
    def by_genre(self, request):
        genre_id = request.query_params.get('genre_id')
        if not genre_id:
            return Response({'error': 'genre_id parameter is required'}, 
                         status=status.HTTP_400_BAD_REQUEST)
        
        tracks = Track.objects.filter(genres__id=genre_id)
        serializer = self.get_serializer(tracks, many=True)
        return Response(serializer.data)

def media_stream(request, path):
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404

    range_header = request.META.get('HTTP_RANGE', '').strip()
    if not range_header:
        return FileResponse(open(file_path, 'rb'))

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

    data = None
    with open(file_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    resp = HttpResponse(data, status=206, content_type='video/mp4')
    resp['Content-Range'] = f'bytes {byte1}-{byte1+length-1}/{size}'
    resp['Accept-Ranges'] = 'bytes'
    resp['Content-Length'] = str(length)
    return resp 