from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/', include('authentication.urls')),
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/", include("user.urls")),
    path("api/", include("music.urls")),
]
