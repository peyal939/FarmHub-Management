from rest_framework.permissions import BasePermission


class IsAgentForRelatedFarm(BasePermission):

    message = "You must be the assigned Agent for this farm."

    def _is_agent(self, user):
        if not user or not user.is_authenticated:
            return False
        # superusers/staff pass here to avoid blocking
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True
        role = getattr(user, "role", None)
        return role == getattr(user.__class__, "Roles").AGENT

    def has_permission(self, request, view):
        user = request.user
        return self._is_agent(user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        # Superusers/staff allowed
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True
        if not self._is_agent(user):
            return False

        # Determine farm from object
        farm_id = None
        try:
            # Cow -> has farm
            if hasattr(obj, "farm") and getattr(obj.farm, "id", None) is not None:
                farm_id = obj.farm.id
            # Activity/MilkRecord -> obj.cow.farm
            elif hasattr(obj, "cow") and hasattr(obj.cow, "farm"):
                farm_id = getattr(obj.cow.farm, "id", None)
        except Exception:
            return False

        if farm_id is None:
            return False

        # Lazy import to avoid circulars
        try:
            from farms.models import Farm

            return Farm.objects.filter(id=farm_id, agent_id=user.id).exists()
        except Exception:
            return False


class IsFarmerAndCowOwner(BasePermission):

    message = "You must be the owner (Farmer) of this cow or related record."

    def _is_farmer(self, user):
        if not user or not user.is_authenticated:
            return False
        role = getattr(user, "role", None)
        return role == getattr(user.__class__, "Roles").FARMER

    def has_permission(self, request, view):
        user = request.user
        # Allow access to list/create only if farmer; object check happens in has_object_permission
        return self._is_farmer(user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not self._is_farmer(user):
            return False
        # obj can be Cow, Activity, or MilkRecord (via view usage)
        cow = None
        try:
            from livestock.models import Cow, Activity
            from production.models import MilkRecord

            if hasattr(obj, "owner") and hasattr(obj, "farm"):
                # Cow
                cow = obj
            elif hasattr(obj, "cow") and isinstance(obj, Activity):
                cow = obj.cow
            elif hasattr(obj, "cow"):
                # MilkRecord (has cow FK)
                cow = obj.cow
        except Exception:
            pass
        if cow is None:
            return False
        # Check ownership
        farmer_profile = getattr(cow, "owner", None)
        user_id = getattr(getattr(farmer_profile, "user", None), "id", None)
        return user_id == user.id
