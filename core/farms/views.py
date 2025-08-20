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
    permission_classes = [IsAuthenticated]

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

    def perform_create(self, serializer):
        """
        Allow:
        - SuperAdmin/staff: create any mapping.
        - Agent: only create profiles for farms they manage (farm.agent_id == request.user.id).
        - Farmer: not allowed.
        """
        user = self.request.user
        # Superadmin/staff bypass
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return serializer.save()

        role = getattr(user, "role", None)
        if role == getattr(user.__class__, "Roles").AGENT:
            farm_id = self.request.data.get("farm")
            if not farm_id:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"farm": "This field is required."})
            # Verify this farm belongs to the agent
            if not Farm.objects.filter(id=farm_id, agent_id=user.id).exists():
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "You can only onboard farmers to your own farms."
                )
            return serializer.save()

        # Farmers (and others) cannot create profiles
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Not allowed to create farmer profiles.")

    def perform_update(self, serializer):
        user = self.request.user
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return serializer.save()
        role = getattr(user, "role", None)
        if role == getattr(user.__class__, "Roles").AGENT:
            # Ensure updated farm remains within agent's management
            new_farm_id = self.request.data.get("farm")
            if (
                new_farm_id
                and not Farm.objects.filter(id=new_farm_id, agent_id=user.id).exists()
            ):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You can only reassign within your farms.")
            return serializer.save()
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Not allowed to update farmer profiles.")
