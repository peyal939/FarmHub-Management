from rest_framework.routers import DefaultRouter
from .views import UserViewSet

app_name = "accounts"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = router.urls
