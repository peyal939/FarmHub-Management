from rest_framework import serializers
from .models import Cow, Activity
from farms.serializers import FarmSerializer


class CowSerializer(serializers.ModelSerializer):
    farm = FarmSerializer(read_only=True)
    farm_id = serializers.IntegerField(write_only=True)
    owner_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Cow
        fields = ["id", "tag", "breed", "dob", "farm", "farm_id", "owner_id"]
        read_only_fields = ["id", "farm"]

    def validate_farm_id(self, value):
        from farms.models import Farm

        if not Farm.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Farm not found.")
        return value

    def validate_owner_id(self, value):
        if value is None:
            return value
        from farms.models import FarmerProfile

        if not FarmerProfile.objects.filter(pk=value).exists():
            raise serializers.ValidationError("FarmerProfile not found.")
        return value

    def create(self, validated_data):
        farm_id = validated_data.pop("farm_id")
        owner_id = validated_data.pop("owner_id", None)
        validated_data["farm_id"] = farm_id
        if owner_id is not None:
            validated_data["owner_id"] = owner_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        farm_id = validated_data.pop("farm_id", None)
        owner_id = validated_data.pop("owner_id", None)  # may be omitted by farmer
        if farm_id is not None:
            instance.farm_id = farm_id
        if owner_id is not None:
            instance.owner_id = owner_id
        return super().update(instance, validated_data)


class ActivitySerializer(serializers.ModelSerializer):
    cow_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Activity
        fields = ["id", "cow_id", "type", "notes", "date"]
        read_only_fields = ["id"]

    def validate_cow_id(self, value):
        if not Cow.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Cow not found.")
        return value

    def create(self, validated_data):
        cow_id = validated_data.pop("cow_id")
        validated_data["cow_id"] = cow_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        cow_id = validated_data.pop("cow_id", None)
        if cow_id is not None:
            instance.cow_id = cow_id
        return super().update(instance, validated_data)
