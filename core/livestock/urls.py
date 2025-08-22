from rest_framework.routers import DefaultRouter
from .views import CowViewSet, ActivityViewSet

app_name = "livestock"

router = DefaultRouter()
router.register(r"cows", CowViewSet, basename="cow")
router.register(r"activities", ActivityViewSet, basename="activity")

urlpatterns = router.urls
