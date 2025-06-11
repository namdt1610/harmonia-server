import os, mimetypes, re
from django.conf import settings
from django.http import FileResponse, HttpResponse
import urllib.parse

def resolve_file_path(file_name: str):
    paths = [
        file_name.lstrip('/'),
        urllib.parse.unquote(file_name.lstrip('/')),
        os.path.join('tracks', os.path.basename(file_name)),
        os.path.join('tracks', urllib.parse.unquote(os.path.basename(file_name))),
    ]
    for p in paths:
        abs_path = os.path.join(settings.MEDIA_ROOT, p)
        if os.path.exists(abs_path):
            return abs_path
    return None

def stream_file_with_range(request, file_path):
    size = os.path.getsize(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or 'audio/mpeg'
    range_header = request.META.get('HTTP_RANGE', '')

    if match := re.match(r'bytes=(\d+)-(\d*)', range_header):
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else size - 1
        length = end - start + 1
        with open(file_path, 'rb') as f:
            f.seek(start)
            data = f.read(length)
        response = HttpResponse(data, status=206, content_type=content_type)
        response['Content-Range'] = f'bytes {start}-{end}/{size}'
        response['Content-Length'] = str(length)
        response['Accept-Ranges'] = 'bytes'
        return response

    return FileResponse(open(file_path, 'rb'), content_type=content_type)
