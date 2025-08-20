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
