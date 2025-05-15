from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/", include("user.urls")),
    path("api/", include("favorites.urls")),
    path("api/", include("music.urls")),
    # path("api/", include("playlists.urls")),
    path("api/chat/", include("chatbot.urls")),
]
