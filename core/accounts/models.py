from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
	class Roles(models.TextChoices):
		SUPERADMIN = 'SUPERADMIN', 'SuperAdmin'
		AGENT = 'AGENT', 'Agent'
		FARMER = 'FARMER', 'Farmer'

	role = models.CharField(
		max_length=20,
		choices=Roles.choices,
		default=Roles.FARMER,
		help_text="Role of the user in the system"
	)

	def __str__(self) -> str:
		return f"{self.username} ({self.get_role_display()})"

# Create your models here.
