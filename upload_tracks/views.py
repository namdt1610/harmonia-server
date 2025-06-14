from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from tracks.models import Track
from artists.models import Artist
from albums.models import Album
from django.core.files.base import ContentFile
import os

class UploadTrackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get form data
            file = request.FILES.get('file')
            title = request.data.get('title')
            artist_id = request.data.get('artist')
            album_id = request.data.get('album')
            duration = request.data.get('duration')

            if not all([file, title, artist_id]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get artist
            try:
                artist = Artist.objects.get(id=artist_id)
            except Artist.DoesNotExist:
                return Response(
                    {'error': 'Artist not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get album if provided
            album = None
            if album_id:
                try:
                    album = Album.objects.get(id=album_id)
                    if album.artist != artist:
                        return Response(
                            {'error': 'Album does not belong to the selected artist'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Album.DoesNotExist:
                    return Response(
                        {'error': 'Album not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Create track
            track = Track.objects.create(
                title=title,
                artist=artist,
                album=album,
                duration=duration,
                is_downloadable=True
            )

            # Save file
            track.file.save(file.name, ContentFile(file.read()), save=True)

            return Response({
                'message': 'Track uploaded successfully',
                'track_id': track.id,
                'file_url': request.build_absolute_uri(track.file.url)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 