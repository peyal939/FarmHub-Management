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

    def perform_create(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        # Superadmin/staff bypass
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            serializer.save()
            return

        farm_id = self.request.data.get("farm_id")
        owner_id = self.request.data.get("owner_id")
        if role == getattr(user.__class__, "Roles").AGENT:
            # Agent can only create within managed farms, any farmer under those farms
            from farms.models import Farm, FarmerProfile
            if not farm_id or not Farm.objects.filter(id=farm_id, agent_id=user.id).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only add cows to your managed farms.")
            if owner_id and not FarmerProfile.objects.filter(id=owner_id, farm_id=farm_id).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"owner_id": "Owner must belong to the same farm."})
            serializer.save()
            return

        if role == getattr(user.__class__, "Roles").FARMER:
            # Force owner_id to the farmer's own profile; enforce farm match
            from farms.models import FarmerProfile
            try:
                fp = FarmerProfile.objects.select_related("farm").get(user_id=user.id)
            except FarmerProfile.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have a farmer profile.")
            if not farm_id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"farm_id": "This field is required."})
            if int(farm_id) != int(fp.farm_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only enroll cows under your own farm.")
            # Save with enforced owner
            serializer.save(owner_id=fp.id)
            return

        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Not allowed to create cows.")

    def perform_update(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return serializer.save()
        farm_id = self.request.data.get("farm_id")
        owner_id = self.request.data.get("owner_id")
        if role == getattr(user.__class__, "Roles").AGENT:
            from farms.models import Farm, FarmerProfile
            if farm_id and not Farm.objects.filter(id=farm_id, agent_id=user.id).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only keep cows within your managed farms.")
            if farm_id and owner_id and not FarmerProfile.objects.filter(id=owner_id, farm_id=farm_id).exists():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"owner_id": "Owner must belong to the same farm."})
            return serializer.save()
        if role == getattr(user.__class__, "Roles").FARMER:
            # Farmers cannot change owner to someone else, and must stay in their farm
            from farms.models import FarmerProfile
            try:
                fp = FarmerProfile.objects.get(user_id=user.id)
            except FarmerProfile.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have a farmer profile.")
            if farm_id and int(farm_id) != int(fp.farm_id):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You must keep the cow under your own farm.")
            # Force owner to self if trying to change
            if owner_id and int(owner_id) != int(fp.id):
                return serializer.save(owner_id=fp.id)
            return serializer.save()
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Not allowed to update cows.")


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

    def perform_create(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return serializer.save()
        cow_id = self.request.data.get("cow_id")
        if role == getattr(user.__class__, "Roles").AGENT:
            from livestock.models import Cow
            if not Cow.objects.filter(id=cow_id, farm__agent_id=user.id).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only log activities for cows in your farms.")
            return serializer.save()
        if role == getattr(user.__class__, "Roles").FARMER:
            from farms.models import FarmerProfile
            from livestock.models import Cow
            try:
                fp = FarmerProfile.objects.get(user_id=user.id)
            except FarmerProfile.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You do not have a farmer profile.")
            if not Cow.objects.filter(id=cow_id, owner_id=fp.id).exists():
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only log activities for your own cows.")
            return serializer.save()
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Not allowed to create activities.")
