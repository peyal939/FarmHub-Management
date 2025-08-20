from rest_framework import serializers
from .models import MilkRecord
from livestock.models import Cow


class MilkRecordSerializer(serializers.ModelSerializer):
    cow_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MilkRecord
        fields = ['id', 'cow_id', 'date', 'liters']
        read_only_fields = ['id']

    def validate_cow_id(self, value):
        if not Cow.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Cow not found.')
        return value

    def create(self, validated_data):
        cow_id = validated_data.pop('cow_id')
        validated_data['cow_id'] = cow_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        cow_id = validated_data.pop('cow_id', None)
        if cow_id is not None:
            instance.cow_id = cow_id
        return super().update(instance, validated_data)
