from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from tracks.views import media_stream


# === Basic Health Check & Homepage ===
def health_check(_):  # clean: request không xài
    return HttpResponse("OK")

def home(_):  # clean: request không xài
    return HttpResponse("Hello World, I'm Harmonia Server, I'm working!")


urlpatterns = [
    # Home + Health
    path("", home),
    path("api/health/", health_check),

    # Admin
    path("admin/", admin.site.urls),
    path("api/admin/", include("admin_api.urls")),

    # Auth
    path("api/auth/", include("authentication.urls")),

    # Feature APIs
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

    # Media (Custom stream handler)
    path("media/<path:path>", media_stream, name="media_stream"),
]

# === Static files in DEBUG ===
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
