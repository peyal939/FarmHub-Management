from rest_framework import viewsets
from .models import Cow, Activity
from .serializers import CowSerializer, ActivitySerializer


class CowViewSet(viewsets.ModelViewSet):
    queryset = Cow.objects.select_related("farm", "owner").all()
    serializer_class = CowSerializer


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related("cow").all()
    serializer_class = ActivitySerializer
