from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Cow, Activity
from .serializers import CowSerializer, ActivitySerializer
from .permissions import IsFarmerAndCowOwner, IsAgentForRelatedFarm
from farms.permissions import IsSuperAdmin


class CowViewSet(viewsets.ModelViewSet):
    queryset = Cow.objects.select_related("farm", "owner").all()
    serializer_class = CowSerializer
    # SuperAdmin OR (Farmer owns the cow) OR (Agent manages the farm)
    permission_classes = [
        IsAuthenticated,
        (IsSuperAdmin | IsFarmerAndCowOwner | IsAgentForRelatedFarm),
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Superusers/staff see all
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return qs
        role = getattr(user, "role", None)
        # Agents: cows within their farms
        if role == getattr(user.__class__, "Roles").AGENT:
            return qs.filter(farm__agent_id=user.id)
        # Farmers: only cows they own
        if role == getattr(user.__class__, "Roles").FARMER:
            return qs.filter(owner__user_id=user.id)
        return qs.none()


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related("cow").all()
    serializer_class = ActivitySerializer
    permission_classes = [
        IsAuthenticated,
        (IsSuperAdmin | IsFarmerAndCowOwner | IsAgentForRelatedFarm),
    ]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return qs
        role = getattr(user, "role", None)
        if role == getattr(user.__class__, "Roles").AGENT:
            return qs.filter(cow__farm__agent_id=user.id)
        if role == getattr(user.__class__, "Roles").FARMER:
            return qs.filter(cow__owner__user_id=user.id)
        return qs.none()
