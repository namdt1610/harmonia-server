from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('authentication.urls')),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/auth/", include("authentication.urls")),
    path("api/", include("user.urls")),
    path("api/", include("music.urls")),
]
