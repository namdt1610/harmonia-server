from rest_framework.routers import DefaultRouter
from .views import QueueViewSet

router = DefaultRouter()
router.register(r'queue', QueueViewSet, basename='queue')

urlpatterns = router.urls 