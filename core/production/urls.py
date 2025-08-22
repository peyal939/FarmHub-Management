from rest_framework.routers import DefaultRouter
from .views import MilkRecordViewSet

app_name = "production"

router = DefaultRouter()
router.register(r"milk-records", MilkRecordViewSet, basename="milkrecord")

urlpatterns = router.urls
