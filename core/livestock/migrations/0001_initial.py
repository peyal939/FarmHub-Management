import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("farms", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cow",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("tag", models.CharField(max_length=50)),
                ("breed", models.CharField(max_length=100)),
                ("dob", models.DateField(blank=True, null=True)),
                (
                    "farm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cows",
                        to="farms.farm",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cows",
                        to="farms.farmerprofile",
                    ),
                ),
            ],
            options={
                "unique_together": {("farm", "tag")},
            },
        ),
        migrations.CreateModel(
            name="Activity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("vaccination", "Vaccination"),
                            ("birth", "Birth"),
                            ("health", "Health"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("date", models.DateField()),
                (
                    "cow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activities",
                        to="livestock.cow",
                    ),
                ),
            ],
        ),
    ]
