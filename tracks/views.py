from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, FileResponse, Http404
from django.conf import settings
import os
from .models import Track
from user_activity.models import UserActivity, PlayHistory
from .serializers import TrackSerializer
from .services import TrackService, TrackFileService
from .responses import TrackResponseHandler
from permissions.permissions import HasCustomPermission
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

logger = logging.getLogger(__name__)

"""
serializers_class chuyển đổi dữ liệu từ model thành dữ liệu JSON
permission_classes: kiểm tra quyền truy cập của người dùng
"""
class TrackViewSet(viewsets.ModelViewSet):
    """
    RESTful Track management ViewSet.
    Provides comprehensive track management functionality including streaming, downloading,
    and analytics tracking.
    """
    serializer_class = TrackSerializer
    permission_classes = [IsAuthenticated, HasCustomPermission]
    swagger_tags = ['Tracks']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.track_service = None
        self.response_handler = TrackResponseHandler()
    
    def initialize_request(self, request, *args, **kwargs):
        """Initialize request with user context and services."""
        request = super().initialize_request(request, *args, **kwargs)
        self.track_service = TrackService(user=request.user)
        return request
    
    def get_queryset(self):
        # Skip service call during schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Track.objects.none()
            
        filters = self.request.query_params.dict()
        return self.track_service.retrieve_tracks_by_criteria(filters)
    
    @property
    def required_permission(self):
        """Map actions to required permissions."""
        mapping = {
            'create': 'add_track',
            'update': 'edit_track',
            'partial_update': 'edit_track',
            'destroy': 'delete_track',
            'list': 'view_track',
            'retrieve': 'view_track',
        }
        perm = mapping.get(self.action)
        if not perm:
            logger.warning(f"No permission code defined for action: {self.action} in {self.__class__.__name__}")
        return perm

    def get_permissions(self):
        """Get required permissions for the current action."""
        self.required_permission = self.required_permission
        return [permission() for permission in self.permission_classes]
    
    def update(self, request, *args, **kwargs):
        """Update track with play or download count."""
        track = self.get_object()
        if 'play_count' in request.data:
            self.track_service.record_track_play_event(track)
            return self.response_handler.create_success_response(message='Play count incremented')
        elif 'download_count' in request.data:
            self.track_service.record_track_download_event(track)
            return self.response_handler.create_success_response(message='Download count incremented')
        return super().update(request, *args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        """List tracks with optional filtering."""
        # Handle special list endpoints
        if request.query_params.get('type') == 'top':
            tracks = self.track_service.retrieve_top_performing_tracks()
            serializer = self.get_serializer(tracks, many=True)
            return self.response_handler.create_success_response(data=serializer.data)
            
        if request.query_params.get('type') == 'trending':
            tracks = self.track_service.retrieve_trending_tracks()
            serializer = self.get_serializer(tracks, many=True)
            return self.response_handler.create_success_response(data=serializer.data)
            
        if request.query_params.get('type') == 'recent':
            tracks = self.track_service.retrieve_recently_added_tracks()
            serializer = self.get_serializer(tracks, many=True)
            return self.response_handler.create_success_response(data=serializer.data)
            
        if request.query_params.get('type') == 'current':
            track = self.track_service.retrieve_currently_playing_track()
            if not track:
                return self.response_handler.create_not_found_response('No track is currently playing')
            serializer = self.get_serializer(track)
            return self.response_handler.create_success_response(data=serializer.data)
            
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Stream a track with range request support",
        responses={
            200: TrackSerializer(),
            404: "Track not found",
            500: "Internal server error"
        }
    )
    @action(detail=True, methods=['get'])
    def stream(self, request, pk=None):
        """Stream a track with range request support."""
        try:
            track = self.get_object()
            file_path = TrackFileService.resolve_track_file_path(track)
            
            if not file_path:
                return self.response_handler.create_not_found_response('Track file not found')
                
            content_type = TrackFileService.determine_file_content_type(file_path)
            range_header = request.META.get('HTTP_RANGE')
            
            if range_header:
                range_result, file_size = TrackFileService.process_range_request(file_path, range_header)
                if range_result:
                    start, end = range_result
                    return self.response_handler.create_partial_content_response(
                        file_path, start, end, file_size, content_type
                    )
            
            return self.response_handler.create_file_download_response(file_path, content_type)
            
        except Exception as e:
            logger.error(f"Error streaming track: {str(e)}")
            return self.response_handler.create_error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Download a track",
        responses={
            200: TrackSerializer(),
            403: "Track not downloadable",
            404: "Track not found"
        }
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a track."""
        track = self.get_object()
        
        if not track.is_downloadable:
            return self.response_handler.create_forbidden_response('This track is not available for download')
        
        self.track_service.record_track_download_event(track)
        
        file_path = TrackFileService.resolve_track_file_path(track)
        if not file_path:
            return self.response_handler.create_not_found_response('Track file not found')
            
        filename = os.path.basename(file_path)
        return self.response_handler.create_file_download_response(
            file_path,
            'audio/mpeg',
            filename=filename,
            as_attachment=True
        )
    
    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Get video information for a track",
        responses={
            200: TrackSerializer(),
            404: "No video available"
        }
    )
    @action(detail=True, methods=['get'])
    def video(self, request, pk=None):
        """Retrieve video information for a track."""
        track = self.get_object()
        
        if not track.music_video:
            return self.response_handler.create_not_found_response('No video available for this track')
        
        return self.response_handler.create_success_response(data={
            'video_url': request.build_absolute_uri(track.music_video.url),
            'thumbnail': request.build_absolute_uri(track.video_thumbnail.url) if track.video_thumbnail else None
        })

    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Stream media files with range request support",
        responses={
            200: TrackSerializer(),
            404: "Media not found",
            500: "Internal server error"
        }
    )
    @action(detail=False, methods=['get'], url_path='media/(?P<path>.*)')
    def media_stream(self, request, path=None):
        """Stream media files with range request support."""
        try:
            return TrackFileService.stream_media_file(request, path)
        except Http404 as e:
            return self.response_handler.create_not_found_response(str(e))
        except Exception as e:
            logger.error(f"Error streaming media file: {str(e)}")
            return self.response_handler.create_error_response(
                str(e), 
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Get a list of tracks with optional filtering",
        responses={
            200: TrackSerializer(many=True),
            400: "Bad Request"
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Create a new track",
        request_body=TrackSerializer(),
        responses={
            201: TrackSerializer(),
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Get a specific track by ID",
        responses={
            200: TrackSerializer(),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Update a track partially",
        request_body=TrackSerializer(),
        responses={
            200: TrackSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Update a track",
        request_body=TrackSerializer(),
        responses={
            200: TrackSerializer(),
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['Tracks'],
        operation_description="Delete a track",
        responses={
            204: "No Content",
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs) 