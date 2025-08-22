from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.utils.functional import cached_property


class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Treat Django superusers as super admins as well
        if getattr(user, "is_superuser", False):
            return True
        role = getattr(user, "role", None)
        return role == getattr(user.__class__, "Roles").SUPERADMIN

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsAgentAndOwner(BasePermission):

    message = "You must be the assigned Agent for this farm."

    def has_permission(self, request, view):
        user = request.user
        # Allow superusers/staff
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True
        # Only authenticated agents allowed beyond this
        if not user.is_authenticated:
            return False
        # user must have role attribute; avoid circular import
        role = getattr(user, "role", None)
        if role != getattr(user.__class__, "Roles").AGENT:
            return False
        # POST create: ensure if agent_id in payload, it matches the agent
        if request.method == "POST":
            agent_id = request.data.get("agent_id")
            # If client does not send agent_id, we'll set it in the viewset; allow
            return True if agent_id is None else str(agent_id) == str(user.id)
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True
        if not user.is_authenticated:
            return False
        role = getattr(user, "role", None)
        if role != getattr(user.__class__, "Roles").AGENT:
            return False
        # For reads/writes, user must be the assigned agent on the farm object
        farm = obj
        return getattr(farm, "agent_id", None) == user.id


class IsAgentAndFarmOwner(IsAgentAndOwner):
    pass


class IsSuperAdminOrAgent(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True
        role = getattr(user, "role", None)
        if role == getattr(user.__class__, "Roles").SUPERADMIN:
            return True
        return role == getattr(user.__class__, "Roles").AGENT

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
