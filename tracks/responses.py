from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, FileResponse
import logging

logger = logging.getLogger(__name__)

class TrackResponseHandler:
    @staticmethod
    def create_success_response(data=None, message=None, status_code=status.HTTP_200_OK):
        response_data = {'status': 'success'}
        if data is not None:
            response_data['data'] = data
        if message:
            response_data['message'] = message
        return Response(response_data, status=status_code)

    @staticmethod
    def create_error_response(message, status_code=status.HTTP_400_BAD_REQUEST):
        return Response({
            'status': 'error',
            'message': message
        }, status=status_code)

    @staticmethod
    def create_not_found_response(message="Resource not found"):
        return Response({
            'status': 'error',
            'message': message
        }, status=status.HTTP_404_NOT_FOUND)

    @staticmethod
    def create_forbidden_response(message="Access denied"):
        return Response({
            'status': 'error',
            'message': message
        }, status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def create_file_download_response(file_path, content_type, filename=None, as_attachment=False):
        try:
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type
            )
            if filename:
                response['Content-Disposition'] = f'{"attachment" if as_attachment else "inline"}; filename="{filename}"'
            return response
        except Exception as e:
            logger.error(f"Error serving file {file_path}: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error serving file'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def create_partial_content_response(file_path, start, end, file_size, content_type):
        try:
            with open(file_path, 'rb') as f:
                f.seek(start)
                data = f.read(end - start + 1)

            response = HttpResponse(
                data,
                status=status.HTTP_206_PARTIAL_CONTENT,
                content_type=content_type
            )
            response['Content-Length'] = str(end - start + 1)
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            return response
        except Exception as e:
            logger.error(f"Error serving range for file {file_path}: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error serving file range'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 