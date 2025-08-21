from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from .models import User
from .serializers import UserSerializer


class IsSuperAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return True
        # Allow custom SUPERADMIN role as well
        role = getattr(user, 'role', None)
        try:
            return role == user.Roles.SUPERADMIN
        except Exception:
            return False


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrStaff]
