from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from tracks.views import media_stream

def health_check():
    return HttpResponse("OK")

def home():
    return HttpResponse("Hello World, I'm Harmonia Server, I'm working!")

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/", include("user.urls")),
    path("api/", include("favorites.urls")),
    path("api/", include("music.urls")),
    path("api/", include("playlists.urls")),
    path("api/", include("tracks.urls")),
    path("api/", include("albums.urls")),
    path("api/", include("artists.urls")),
    path("api/", include("genres.urls")),
    path("api/", include("user_activity.urls")),
    path("api/", include("analytics.urls")),
    path("api/", include("stream_queue.urls")),
    path("api/chat/", include("chatbot.urls")),
    path("api/admin/", include("admin_api.urls")),
    path("api/health/", health_check),
    path('media/<path:path>', media_stream, name='media_stream'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)