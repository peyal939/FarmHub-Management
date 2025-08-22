from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Auth (JWT)
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # App routes (namespaced)
    path(
        "api/",
        include(
            [
                path("", include("accounts.urls", namespace="accounts")),
                path("", include("farms.urls", namespace="farms")),
                path("", include("livestock.urls", namespace="livestock")),
                path("", include("production.urls", namespace="production")),
            ]
        ),
    ),
    # Optionally mirror at root for now (can be removed later)
    path(
        "",
        include(
            [
                path("", include("accounts.urls", namespace="accounts-root")),
                path("", include("farms.urls", namespace="farms-root")),
                path("", include("livestock.urls", namespace="livestock-root")),
                path("", include("production.urls", namespace="production-root")),
            ]
        ),
    ),
    # Simple health/ping endpoint
    path("healthz/", lambda request: JsonResponse({"status": "ok"}), name="healthz"),
]
