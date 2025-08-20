from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet
from farms.views import FarmViewSet, FarmerProfileViewSet
from livestock.views import CowViewSet, ActivityViewSet
from production.views import MilkRecordViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"farms", FarmViewSet, basename="farm")
router.register(r"farmer-profiles", FarmerProfileViewSet, basename="farmerprofile")
router.register(r"cows", CowViewSet, basename="cow")
router.register(r"activities", ActivityViewSet, basename="activity")
router.register(r"milk-records", MilkRecordViewSet, basename="milkrecord")

urlpatterns = [
    path("admin/", admin.site.urls),
    # DRF browsable API at both / and /api/
    path("api/", include(router.urls)),
    path("", include(router.urls)),
    # Simple health/ping endpoint
    path("healthz/", lambda request: JsonResponse({"status": "ok"}), name="healthz"),
]
