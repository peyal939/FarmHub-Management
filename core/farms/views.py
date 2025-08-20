from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Farm, FarmerProfile
from .serializers import FarmSerializer, FarmerProfileSerializer
from .permissions import IsAgentAndFarmOwner, IsSuperAdmin


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.select_related("agent").all().order_by("name")
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated, (IsSuperAdmin | IsAgentAndFarmOwner)]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Superuser/staff see all; agents see only their farms; others see none
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return qs
        role = getattr(user, "role", None)
        if user.is_authenticated and role == getattr(user.__class__, "Roles").AGENT:
            return qs.filter(agent_id=user.id)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        # If agent creates a farm without specifying agent_id, set it to themselves
        agent_id = self.request.data.get("agent_id")
        if not agent_id and user.is_authenticated:
            serializer.save(agent_id=user.id)
        else:
            serializer.save()


class FarmerProfileViewSet(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.select_related("user", "farm").all()
    serializer_class = FarmerProfileSerializer
    permission_classes = [IsAuthenticated, (IsSuperAdmin,)]

    def get_permissions(self):
        # Custom handling: allow Agent and Farmer in a scoped way below
        return [p() if isinstance(p, type) else p for p in self.permission_classes]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Superusers/staff see all
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return qs
        role = getattr(user, "role", None)
        if role == getattr(user.__class__, "Roles").AGENT:
            return qs.filter(farm__agent_id=user.id)
        if role == getattr(user.__class__, "Roles").FARMER:
            return qs.filter(user_id=user.id)
        return qs.none()
