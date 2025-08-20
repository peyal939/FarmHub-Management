from django.conf import settings
from django.db import models


class Farm(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_farms',
        help_text='Agent (User) managing this farm'
    )

    def __str__(self) -> str:
        return self.name


class FarmerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='farmer_profile'
    )
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name='farmers'
    )

    def __str__(self) -> str:
        return f"FarmerProfile<{self.user.username} @ {self.farm.name}>"
