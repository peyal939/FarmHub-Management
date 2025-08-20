from rest_framework import viewsets
from .models import MilkRecord
from .serializers import MilkRecordSerializer


class MilkRecordViewSet(viewsets.ModelViewSet):
	queryset = MilkRecord.objects.select_related('cow').all().order_by('-date')
	serializer_class = MilkRecordSerializer
