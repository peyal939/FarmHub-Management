from rest_framework.routers import DefaultRouter
from .views import FarmViewSet, FarmerProfileViewSet

app_name = "farms"

router = DefaultRouter()
router.register(r"farms", FarmViewSet, basename="farm")
router.register(r"farmer-profiles", FarmerProfileViewSet, basename="farmerprofile")

urlpatterns = router.urls
