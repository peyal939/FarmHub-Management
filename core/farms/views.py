from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from .models import Farm, FarmerProfile
from .serializers import FarmSerializer, FarmerProfileSerializer


class FarmRBACPermission(BasePermission):
    """Central permission logic for Farm operations.

    - Read: authenticated users; queryset further scopes results.
    - Write (create/update/delete): only SuperAdmin or Agent.
    - Object-level write: Agent only if they are the assigned agent.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if getattr(user, "is_superuser", False) or (
            Roles and role == Roles.SUPERADMIN
        ):
            return True
        return Roles and role == Roles.AGENT

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if getattr(user, "is_superuser", False) or (
            Roles and role == Roles.SUPERADMIN
        ):
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
        if getattr(user, "is_superuser", False) or (
            Roles and role == Roles.SUPERADMIN
        ):
            return qs
        if user.is_authenticated and Roles and role == Roles.AGENT:
            return qs.filter(agent_id=user.id)
        return qs.none()

    # create/update/delete logic enforced by permission + serializer


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

    # create/update constraints are enforced within serializer validation
