from rest_framework.permissions import BasePermission


class IsFarmerAndCowOwner(BasePermission):
    """
    Allows access if the user's role is FARMER and the cow/activity/milk record belongs to them.
    Assumes:
      - Cow has owner -> FarmerProfile -> user
      - Activity has cow FK
      - MilkRecord checked at its own view via cow relation
    """

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
