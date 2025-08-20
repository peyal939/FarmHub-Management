from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import MilkRecord
from .serializers import MilkRecordSerializer
from livestock.permissions import IsFarmerAndCowOwner
from farms.permissions import IsSuperAdmin


class MilkRecordViewSet(viewsets.ModelViewSet):
    queryset = MilkRecord.objects.select_related("cow").all().order_by("-date")
    serializer_class = MilkRecordSerializer
    permission_classes = [IsAuthenticated, (IsSuperAdmin | IsFarmerAndCowOwner)]
