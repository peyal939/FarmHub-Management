from rest_framework import viewsets
from .models import Farm, FarmerProfile
from .serializers import FarmSerializer, FarmerProfileSerializer


class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.select_related("agent").all().order_by("name")
    serializer_class = FarmSerializer


class FarmerProfileViewSet(viewsets.ModelViewSet):
    queryset = FarmerProfile.objects.select_related("user", "farm").all()
    serializer_class = FarmerProfileSerializer
