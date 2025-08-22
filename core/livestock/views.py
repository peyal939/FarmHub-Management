from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Cow, Activity
from .serializers import CowSerializer, ActivitySerializer
from .permissions import IsFarmerAndCowOwner, IsAgentForRelatedFarm
from farms.permissions import IsSuperAdmin
from farms.models import Farm, FarmerProfile


class CowViewSet(viewsets.ModelViewSet):
    queryset = Cow.objects.select_related("farm", "owner").all()
    serializer_class = CowSerializer
    permission_classes = [
        IsAuthenticated,
        (IsSuperAdmin | IsFarmerAndCowOwner | IsAgentForRelatedFarm),
    ]

    def get_queryset(self):
        qs = Cow.objects.select_related("farm", "owner").all()
        user = self.request.user
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return qs
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if Roles and role == Roles.AGENT:
            return qs.filter(farm__agent_id=user.id)
        if Roles and role == Roles.FARMER:
            return qs.filter(owner__user_id=user.id)
        return qs.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        farm_id = request.data.get("farm_id")
        owner_id = request.data.get("owner_id")

        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"message": "Cow created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        if Roles and role == Roles.AGENT:
            if (
                not farm_id
                or not Farm.objects.filter(id=farm_id, agent_id=user.id).exists()
            ):
                raise PermissionDenied("You can only add cows to your managed farms.")
            if (
                owner_id
                and not FarmerProfile.objects.filter(
                    id=owner_id, farm_id=farm_id
                ).exists()
            ):
                raise ValidationError(
                    {"owner_id": "Owner must belong to the same farm."}
                )
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"message": "Cow created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        if Roles and role == Roles.FARMER:
            try:
                fp = FarmerProfile.objects.select_related("farm").get(user_id=user.id)
            except FarmerProfile.DoesNotExist:
                raise PermissionDenied("You do not have a farmer profile.")
            if not farm_id:
                raise ValidationError({"farm_id": "This field is required."})
            if int(farm_id) != int(fp.farm_id):
                raise PermissionDenied("You can only enroll cows under your own farm.")
            mutable_data = request.data.copy()
            mutable_data["owner_id"] = fp.id
            serializer = self.get_serializer(data=mutable_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"message": "Cow created", "data": serializer.data},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        raise PermissionDenied("Not allowed to create cows.")

    def update(self, request, *args, **kwargs):  # type: ignore[override]
        user = request.user
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        farm_id = request.data.get("farm_id")
        owner_id = request.data.get("owner_id")

        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Cow updated", "data": serializer.data})

        if Roles and role == Roles.AGENT:
            if (
                farm_id
                and not Farm.objects.filter(id=farm_id, agent_id=user.id).exists()
            ):
                raise PermissionDenied(
                    "You can only keep cows within your managed farms."
                )
            if (
                farm_id
                and owner_id
                and not FarmerProfile.objects.filter(
                    id=owner_id, farm_id=farm_id
                ).exists()
            ):
                raise ValidationError(
                    {"owner_id": "Owner must belong to the same farm."}
                )
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Cow updated", "data": serializer.data})

        if Roles and role == Roles.FARMER:
            try:
                fp = FarmerProfile.objects.get(user_id=user.id)
            except FarmerProfile.DoesNotExist:
                raise PermissionDenied("You do not have a farmer profile.")
            if farm_id and int(farm_id) != int(fp.farm_id):
                raise PermissionDenied("You must keep the cow under your own farm.")
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            if owner_id and int(owner_id) != int(fp.id):
                serializer.save(owner_id=fp.id)
            else:
                serializer.save()
            return Response({"message": "Cow updated", "data": serializer.data})

        raise PermissionDenied("Not allowed to update cows.")


class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.select_related("cow").all()
    serializer_class = ActivitySerializer
    permission_classes = [
        IsAuthenticated,
        (IsSuperAdmin | IsFarmerAndCowOwner | IsAgentForRelatedFarm),
    ]

    def get_queryset(self):
        qs = Activity.objects.select_related("cow").all()
        user = self.request.user
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return qs
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        if Roles and role == Roles.AGENT:
            return qs.filter(cow__farm__agent_id=user.id)
        if Roles and role == Roles.FARMER:
            return qs.filter(cow__owner__user_id=user.id)
        return qs.none()

    def create(self, request, *args, **kwargs):  # type: ignore[override]
        user = request.user
        role = getattr(user, "role", None)
        Roles = getattr(user.__class__, "Roles", None)
        cow_id = request.data.get("cow_id")

        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(
                {"message": "Activity logged", "data": serializer.data},
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        if Roles and role == Roles.AGENT:
            if not Cow.objects.filter(id=cow_id, farm__agent_id=user.id).exists():
                raise PermissionDenied(
                    "You can only log activities for cows in your farms."
                )
        elif Roles and role == Roles.FARMER:
            try:
                fp = FarmerProfile.objects.get(user_id=user.id)
            except FarmerProfile.DoesNotExist:
                raise PermissionDenied("You do not have a farmer profile.")
            if not Cow.objects.filter(id=cow_id, owner_id=fp.id).exists():
                raise PermissionDenied("You can only log activities for your own cows.")
        else:
            raise PermissionDenied("Not allowed to create activities.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "Activity logged", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )
