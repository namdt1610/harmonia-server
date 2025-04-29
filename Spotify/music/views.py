from rest_framework import viewsets, permissions, status, serializers
from .models import Artist, Album, Track, Playlist, Genre, Favorite, UserActivity
from .serializers import ArtistSerializer, AlbumSerializer, TrackSerializer, PlaylistSerializer, GenreSerializer, FavoriteSerializer, UserActivitySerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
import os
import logging
from django.db.models import Q
from django.http import FileResponse
from django.conf import settings
# Configure logging
logger = logging.getLogger(__name__)

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "size"
    max_page_size = 100
    
class GlobalSearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get('q', '')
        logger.debug(f"Search query: {query}")

        if not query:
            return Response({"error": "Missing search query"}, status=400)

        tracks = Track.objects.filter(Q(title__icontains=query))
        artists = Artist.objects.filter(Q(name__icontains=query))
        playlists = Playlist.objects.filter(Q(name__icontains=query))

        logger.debug(f"Search results - Tracks: {tracks.count()}, Artists: {artists.count()}, Playlists: {playlists.count()}")

        return Response({
            "tracks": TrackSerializer(tracks, many=True).data,
            "artists": ArtistSerializer(artists, many=True).data,
            "playlists": PlaylistSerializer(playlists, many=True).data
        })
        
class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.AllowAny]  # Mọi người đều có thể xem

class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False)
    def by_artist(self, request):
        artist_id = request.query_params.get('artist_id')
        if artist_id:
            albums = Album.objects.filter(artist_id=artist_id)
            serializer = self.get_serializer(albums, many=True)
            return Response(serializer.data)
        return Response({"error": "artist_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'artist__name']
    
    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        try:
            track = self.get_object()
            
            # Sử dụng urllib để decode URL
            import urllib.parse
            
            # Thử nhiều cách để tìm file
            possible_paths = []
            
            # 1. Đường dẫn chuẩn
            standard_path = os.path.join(settings.MEDIA_ROOT, track.file.name.lstrip('/'))
            possible_paths.append(standard_path)
            
            # 2. Đường dẫn với URL decode
            decoded_name = urllib.parse.unquote(track.file.name)
            decoded_path = os.path.join(settings.MEDIA_ROOT, decoded_name.lstrip('/'))
            possible_paths.append(decoded_path)
            
            # 3. Thử với tên file đơn giản (không có thư mục)
            simple_name = os.path.basename(track.file.name)
            simple_path = os.path.join(settings.MEDIA_ROOT, 'tracks', simple_name)
            possible_paths.append(simple_path)
            
            # 4. Tên file đơn giản được decode
            decoded_simple = urllib.parse.unquote(simple_name)
            decoded_simple_path = os.path.join(settings.MEDIA_ROOT, 'tracks', decoded_simple)
            possible_paths.append(decoded_simple_path)
            
            # In tất cả đường dẫn để debug
            print("Checking these possible paths:")
            for i, path in enumerate(possible_paths):
                print(f"Path {i+1}: {path}")
                if os.path.exists(path):
                    print(f"File found at path {i+1}!")
                    return FileResponse(open(path, 'rb'), content_type="audio/mpeg")
            
            # Nếu không tìm thấy, liệt kê tất cả các file trong thư mục tracks
            print("Files in tracks directory:")
            track_files = os.listdir(os.path.join(settings.MEDIA_ROOT, 'tracks'))
            for file in track_files:
                print(f"- {file}")
            
            return Response({
                "error": "File not found", 
                "file_name": track.file.name,
                "checked_paths": possible_paths
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
        
        return Response({
            'download_url': request.build_absolute_uri(track.file.url),
            'status': 'download count incremented'
        })
    
    @action(detail=True, methods=['get'])
    def video(self, request, pk=None):
        track = self.get_object()
        
        if not track.video_file:
            return Response({'error': 'No video available for this track'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'video_url': request.build_absolute_uri(track.video_file.url),
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

class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticated]  # Chỉ user đăng nhập mới được thao tác

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Gán user tạo playlist

class UploadTrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def upload(self, request):
        try:
            file = request.FILES.get('file')
            artist_id = request.data.get('artist')  # Lấy artist từ request
            duration = request.data.get('duration')  # Lấy duration từ request

            if not file:
                return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not artist_id:
                return Response({'error': 'Artist is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Kiểm tra artist có tồn tại không
            try:
                artist = Artist.objects.get(id=int(artist_id))
            except Artist.DoesNotExist:
                return Response({'error': 'Artist not found'}, status=status.HTTP_400_BAD_REQUEST)

            # Tạo track với artist_id
            track = Track.objects.create(
                file=file, 
                title=file.name, 
                artist=artist,
                duration=int(duration) if duration else None
            )

            return Response({
                "message": "Upload successfully!",
                "file": track.file.url,
                "id": track.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class TrackFileSerializer(serializers.ModelSerializer):
    def validate(self, file):
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in [".mp3", ".wav", ".flac"]:
            raise serializers.ValidationError("Invalid file type")
        if file.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File quá lớn! Giới hạn 50MB.")
        return file
    
    class Meta:
        model = Track
        fields = '__all__'
        
class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        track_id = request.data.get('track')
        
        # Check if the favorite already exists
        existing = Favorite.objects.filter(user=request.user, track_id=track_id).first()
        if existing:
            return Response({'error': 'Track already in favorites'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        response = super().create(request, *args, **kwargs)
        
        # Record user activity
        if response.status_code == status.HTTP_201_CREATED:
            UserActivity.objects.create(
                user=request.user,
                track_id=track_id,
                action='like'
            )
        
        return response
    
    @action(detail=False, methods=['DELETE'])
    def remove(self, request):
        track_id = request.query_params.get('track_id')
        if not track_id:
            return Response({'error': 'track_id parameter is required'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        favorite = Favorite.objects.filter(user=request.user, track_id=track_id).first()
        if not favorite:
            return Response({'error': 'Track not found in favorites'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)