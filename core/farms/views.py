from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Farm, FarmerProfile
from .serializers import FarmSerializer, FarmerProfileSerializer
from .permissions import IsAgentAndFarmOwner, IsSuperAdmin, IsSuperAdminOrAgent


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.select_related("agent").all().order_by("name")
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated, (IsSuperAdmin | IsAgentAndFarmOwner)]

    def get_permissions(self):
        """Tighten create/update/delete: only SuperAdmin or Agent allowed; block Farmers at permission layer."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsSuperAdminOrAgent()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Extra guardrail to prevent Farmers from creating farms via serializer shortcuts."""
        from rest_framework.exceptions import PermissionDenied

        user = request.user
        if (
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None)
            == getattr(user.__class__, "Roles").SUPERADMIN
        ):
            return super().create(request, *args, **kwargs)
        role = getattr(user, "role", None)
        if role == getattr(user.__class__, "Roles").AGENT:
            # If agent passes a different agent_id, block here early
            agent_id = request.data.get("agent_id")
            if agent_id is not None and str(agent_id) != str(user.id):
                raise PermissionDenied(
                    "Agents can only create farms assigned to themselves."
                )
            return super().create(request, *args, **kwargs)
        raise PermissionDenied("Not allowed to create farms.")

    def get_queryset(self):
        # Explicit base queryset to ensure select_related always applies
        qs = Farm.objects.select_related("agent").all().order_by("name")
        user = self.request.user
        # Superuser/SUPERADMIN see all; agents see only their farms; others see none
        if (
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None)
            == getattr(user.__class__, "Roles").SUPERADMIN
        ):
            return qs
        role = getattr(user, "role", None)
        if user.is_authenticated and role == getattr(user.__class__, "Roles").AGENT:
            return qs.filter(agent_id=user.id)
        return qs.none()

    def perform_create(self, serializer):
        """
        Only allow:
        - SuperAdmin: create any farm and assign any agent.
        - Agent: can create farms but only with themselves as agent (agent_id == request.user.id).
        - Farmer/others: not allowed.
        """
        from rest_framework.exceptions import PermissionDenied

        user = self.request.user
        # Superadmin bypass
        if (
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None)
            == getattr(user.__class__, "Roles").SUPERADMIN
        ):
            return serializer.save()

        role = getattr(user, "role", None)
        # Agent can create farm only for themselves
        if role == getattr(user.__class__, "Roles").AGENT:
            agent_id = self.request.data.get("agent_id")
            # If not provided, force to self
            if not agent_id:
                return serializer.save(agent_id=user.id)
            # If provided, must match self
            if str(agent_id) != str(user.id):
                raise PermissionDenied(
                    "Agents can only create farms assigned to themselves."
                )
            return serializer.save()

        # Farmers and others cannot create farms
        raise PermissionDenied("Not allowed to create farms.")

    def perform_update(self, serializer):
        """Prevent agents from reassigning a farm to a different agent."""
        from rest_framework.exceptions import PermissionDenied

        user = self.request.user
        if (
            getattr(user, "is_superuser", False)
            or getattr(user, "role", None)
            == getattr(user.__class__, "Roles").SUPERADMIN
        ):
            return serializer.save()
        role = getattr(user, "role", None)
        if role == getattr(user.__class__, "Roles").AGENT:
            agent_id = self.request.data.get("agent_id")
            if agent_id is not None and str(agent_id) != str(user.id):
                raise PermissionDenied("Agents cannot reassign farms to other agents.")
            return serializer.save()
        raise PermissionDenied("Not allowed to update farms.")


class FarmerProfileViewSet(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.select_related("user", "farm").all()
    serializer_class = FarmerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Explicit base queryset to ensure select_related always applies
        qs = FarmerProfile.objects.select_related("user", "farm").all()
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
