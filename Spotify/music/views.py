from rest_framework import viewsets, permissions, status, serializers
from .models import Artist, Album, Track, Playlist
from .serializers import ArtistSerializer, AlbumSerializer, TrackSerializer, PlaylistSerializer
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.files.base import ContentFile
from .models import Track
from .serializers import TrackSerializer
import os
import logging
logger = logging.getLogger(__name__)

class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.AllowAny]  # Mọi người đều có thể xem

class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [permissions.AllowAny]

class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [permissions.AllowAny]


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
            if not file:
                return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

            file_path = default_storage.save(f"tracks/{file.name}", ContentFile(file.read()))
            file_url = default_storage.url(file_path)

            music = Track.objects.create(file=file_url, title=file.name)

            return Response({"message": "Upload successfully!", "file_url": file_url}, status=status.HTTP_201_CREATED)
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