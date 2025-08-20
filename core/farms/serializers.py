from rest_framework import serializers
from .models import Farm, FarmerProfile
from accounts.serializers import UserSerializer


class FarmSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)
    agent_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Farm
        fields = ['id', 'name', 'location', 'agent', 'agent_id']
        read_only_fields = ['id', 'agent']

    def validate_agent_id(self, value):
        if value is None:
            return value
        from accounts.models import User
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('Agent not found.')
        if user.role != User.Roles.AGENT:
            raise serializers.ValidationError('Selected user is not an AGENT.')
        return value

    def create(self, validated_data):
        agent_id = validated_data.pop('agent_id', None)
        if agent_id is not None:
            validated_data['agent_id'] = agent_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        agent_id = validated_data.pop('agent_id', None)
        if agent_id is not None:
            instance.agent_id = agent_id
        return super().update(instance, validated_data)


class FarmerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FarmerProfile
        fields = ['id', 'user', 'user_id', 'farm']
        read_only_fields = ['id', 'user']

    def validate_user_id(self, value):
        from accounts.models import User
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found.')
        if user.role != User.Roles.FARMER:
            raise serializers.ValidationError('Selected user is not a FARMER.')
        return value

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        validated_data['user_id'] = user_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user_id = validated_data.pop('user_id', None)
        if user_id is not None:
            instance.user_id = user_id
        return super().update(instance, validated_data)
