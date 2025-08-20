from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Cow, Activity
from .serializers import CowSerializer, ActivitySerializer
from .permissions import IsFarmerAndCowOwner
from farms.permissions import IsSuperAdmin


class CowViewSet(viewsets.ModelViewSet):
    queryset = Cow.objects.select_related("farm", "owner").all()
    serializer_class = CowSerializer
    permission_classes = [IsAuthenticated, (IsSuperAdmin | IsFarmerAndCowOwner)]


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related("cow").all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, (IsSuperAdmin | IsFarmerAndCowOwner)]
