from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import MilkRecord
from .serializers import MilkRecordSerializer
from livestock.permissions import IsFarmerAndCowOwner, IsAgentForRelatedFarm
from farms.permissions import IsSuperAdmin


class MilkRecordViewSet(viewsets.ModelViewSet):
    queryset = MilkRecord.objects.select_related("cow").all().order_by("-date")
    serializer_class = MilkRecordSerializer
    permission_classes = [
        IsAuthenticated,
        (IsSuperAdmin | IsFarmerAndCowOwner | IsAgentForRelatedFarm),
    ]

    def get_queryset(self):
        # Explicit base queryset to ensure select_related always applies
        qs = MilkRecord.objects.select_related("cow").all().order_by("-date")
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
            serializer.save()
            return
        cow_id = self.request.data.get("cow_id")
        if role == getattr(user.__class__, "Roles").AGENT:
            from livestock.models import Cow

            if not Cow.objects.filter(id=cow_id, farm__agent_id=user.id).exists():
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "You can only record milk for cows in your farms."
                )
            serializer.save()
            return
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

                raise PermissionDenied("You can only record milk for your own cows.")
            serializer.save()
            return
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Not allowed to create milk records.")

    def perform_update(self, serializer):
        user = self.request.user
        role = getattr(user, "role", None)
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            serializer.save()
            return
        cow_id = self.request.data.get("cow_id")
        if role == getattr(user.__class__, "Roles").AGENT:
            from livestock.models import Cow

            if (
                cow_id
                and not Cow.objects.filter(id=cow_id, farm__agent_id=user.id).exists()
            ):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "You can only manage milk for cows in your farms."
                )
            serializer.save()
            return
        if role == getattr(user.__class__, "Roles").FARMER:
            from farms.models import FarmerProfile
            from livestock.models import Cow

            try:
                fp = FarmerProfile.objects.get(user_id=user.id)
            except FarmerProfile.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You do not have a farmer profile.")
            if cow_id and not Cow.objects.filter(id=cow_id, owner_id=fp.id).exists():
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("You can only manage milk for your own cows.")
            serializer.save()
            return
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Not allowed to update milk records.")
