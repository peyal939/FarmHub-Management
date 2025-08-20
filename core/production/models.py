from django.db import models
from livestock.models import Cow


class MilkRecord(models.Model):
	cow = models.ForeignKey(Cow, on_delete=models.CASCADE, related_name='milk_records')
	date = models.DateField()
	liters = models.DecimalField(max_digits=6, decimal_places=2)
	# recorded_by will be added later during API work (FK to User)

	class Meta:
		unique_together = ("cow", "date")
		ordering = ["-date"]

	def __str__(self) -> str:
		return f"{self.cow.tag} - {self.date} - {self.liters} L"

# Create your models here.
