from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from tracks.views import TrackViewSet
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# === Swagger Configuration ===
schema_view = get_schema_view(
    openapi.Info(
        title="Harmonia API",
        default_version='v1',
        description="API documentation for Harmonia Music Platform",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@harmonia.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url='http://127.0.0.1:8000',
)

# === Basic Health Check & Homepage ===
def health_check(_):  # clean: request không xài
    return HttpResponse("OK")

def home(_):  # clean: request không xài
    return HttpResponse("Hello World, I'm Harmonia Server, I'm working!")


urlpatterns = [
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

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
    path("api/", include("playlists.urls")),
    path("api/", include("tracks.urls")),
    path("api/", include("albums.urls")),
    path("api/", include("artists.urls")),
    path("api/", include("genres.urls")),
    path("api/", include("user_activity.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/", include("stream_queue.urls")),
    path("api/chat/", include("chatbot.urls")),
    path("api/subscriptions/", include("subscription_plans.urls")),

    # Media (Custom stream handler)
    path("media/<path:path>", TrackViewSet.as_view({'get': 'media_stream'}), name="media_stream"),
]

# === Static files in DEBUG ===
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
