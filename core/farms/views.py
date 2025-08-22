from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Farm, FarmerProfile
from .serializers import FarmSerializer, FarmerProfileSerializer


class FarmRBACPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if getattr(user, "is_superuser", False) or (Roles and role == Roles.SUPERADMIN):
            return True
        return Roles and role == Roles.AGENT

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if getattr(user, "is_superuser", False) or (Roles and role == Roles.SUPERADMIN):
            return True
        return Roles and role == Roles.AGENT and obj.agent_id == user.id


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.select_related("agent").all().order_by("name")
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated, FarmRBACPermission]

    def get_queryset(self):
        qs = Farm.objects.select_related("agent").all().order_by("name")
        user = self.request.user
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if getattr(user, "is_superuser", False) or (Roles and role == Roles.SUPERADMIN):
            return qs
        if user.is_authenticated and Roles and role == Roles.AGENT:
            return qs.filter(agent_id=user.id)
        return qs.none()

    def create(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Farm created", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):  # type: ignore[override]
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": "Farm updated", "data": serializer.data})

    def destroy(self, request, *args, **kwargs):  # type: ignore[override]
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Farm deleted"}, status=status.HTTP_204_NO_CONTENT)


class FarmerProfileViewSet(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.select_related("user", "farm").all()
    serializer_class = FarmerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = FarmerProfile.objects.select_related("user", "farm").all()
        user = self.request.user
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return qs
        if Roles and role == Roles.AGENT:
            return qs.filter(farm__agent_id=user.id)
        if Roles and role == Roles.FARMER:
            return qs.filter(user_id=user.id)
        return qs.none()

    def create(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Farmer profile created", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):  # type: ignore[override]
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"message": "Farmer profile updated", "data": serializer.data})

    def destroy(self, request, *args, **kwargs):  # type: ignore[override]
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Farmer profile deleted"}, status=status.HTTP_204_NO_CONTENT
        )
