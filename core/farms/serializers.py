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
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        # Fallback: if no request, behave safely (deny farmer scenarios by requiring explicit agent)
        if user is None or not getattr(user, 'is_authenticated', False):
            raise serializers.ValidationError('Authentication required.')

        # Superadmin/staff: allow, pass through agent_id if provided
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            agent_id = validated_data.pop('agent_id', None)
            if agent_id is not None:
                validated_data['agent_id'] = agent_id
            return super().create(validated_data)

        # Agent: enforce self-assignment only
        role = getattr(user, 'role', None)
        if role == getattr(user.__class__, 'Roles').AGENT:
            agent_id = validated_data.pop('agent_id', None)
            if agent_id is not None and str(agent_id) != str(user.id):
                raise serializers.ValidationError('Agents can only assign themselves as agent.')
            validated_data['agent_id'] = user.id
            return super().create(validated_data)

        # Farmer/others: block
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied('Not allowed to create farms.')

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
