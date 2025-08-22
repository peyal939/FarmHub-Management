from rest_framework import serializers
from .models import Farm, FarmerProfile
from accounts.serializers import UserSerializer


class FarmSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)
    agent_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Farm
        fields = ["id", "name", "location", "agent", "agent_id"]
        read_only_fields = ["id", "agent"]

    def validate_agent_id(self, value):
        if value is None:
            return value
        from accounts.models import User

        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Agent not found.")
        if user.role != User.Roles.AGENT:
            raise serializers.ValidationError("Selected user is not an AGENT.")
        return value

    def validate(self, attrs):
        """Central RBAC validation for create/update on Farm."""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            raise serializers.ValidationError("Authentication required.")
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        creating = self.instance is None

        # Superadmin bypass
        if getattr(user, "is_superuser", False) or (Roles and role == Roles.SUPERADMIN):
            return attrs

        # Agent rules
        if Roles and role == Roles.AGENT:
            agent_id = attrs.pop("agent_id", None)
            if creating:
                if agent_id and str(agent_id) != str(user.id):
                    raise serializers.ValidationError(
                        "Agents can only create farms for themselves."
                    )
                attrs["agent_id"] = user.id
            else:
                # On update, agent_id cannot change to someone else
                if agent_id and str(agent_id) != str(user.id):
                    raise serializers.ValidationError(
                        "Agents cannot reassign farms to other agents."
                    )
            return attrs

        # Farmers / others blocked
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Not allowed to create or modify farms.")

    def update(self, instance, validated_data):
        agent_id = validated_data.pop("agent_id", None)
        if agent_id is not None:
            instance.agent_id = agent_id
        return super().update(instance, validated_data)


class FarmerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FarmerProfile
        fields = ["id", "user", "user_id", "farm"]
        read_only_fields = ["id", "user"]

    def validate_user_id(self, value):
        from accounts.models import User

        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if user.role != User.Roles.FARMER:
            raise serializers.ValidationError("Selected user is not a FARMER.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            raise serializers.ValidationError("Authentication required.")
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        creating = self.instance is None

        # Superadmin/staff bypass
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return attrs

        if Roles and role == Roles.AGENT:
            farm = attrs.get("farm")
            farm_id = getattr(farm, "id", farm) if farm else None
            if not farm_id:
                raise serializers.ValidationError({"farm": "This field is required."})
            from .models import Farm

            if not Farm.objects.filter(id=farm_id, agent_id=user.id).exists():
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied(
                    "You can only manage profiles for your own farms."
                )
            return attrs

        # Farmers cannot create/update profiles themselves
        if creating:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Not allowed to create farmer profiles.")
        return attrs
