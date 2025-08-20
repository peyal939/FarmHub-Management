from django.db import models
from django.conf import settings
from farms.models import FarmerProfile, Farm


class Cow(models.Model):
	tag = models.CharField(max_length=50)
	breed = models.CharField(max_length=100)
	dob = models.DateField(blank=True, null=True)
	farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='cows')
	owner = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='cows')

	class Meta:
		unique_together = ("farm", "tag")

	def __str__(self) -> str:
		return f"{self.tag} ({self.breed})"


class Activity(models.Model):
	class Types(models.TextChoices):
		VACCINATION = 'vaccination', 'Vaccination'
		BIRTH = 'birth', 'Birth'
		HEALTH = 'health', 'Health'
		OTHER = 'other', 'Other'

	cow = models.ForeignKey(Cow, on_delete=models.CASCADE, related_name='activities')
	type = models.CharField(max_length=20, choices=Types.choices)
	notes = models.TextField(blank=True)
	date = models.DateField()

	def __str__(self) -> str:
		return f"{self.get_type_display()} on {self.date} for {self.cow.tag}"

# Create your models here.
