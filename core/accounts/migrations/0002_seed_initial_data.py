from django.db import migrations
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.hashers import make_password


def seed_initial_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Farm = apps.get_model("farms", "Farm")
    FarmerProfile = apps.get_model("farms", "FarmerProfile")
    Cow = apps.get_model("livestock", "Cow")
    Activity = apps.get_model("livestock", "Activity")
    MilkRecord = apps.get_model("production", "MilkRecord")

    superadmin, _ = User.objects.get_or_create(
        username="superadmin",
        defaults={
            "email": "superadmin@farmhub.bd",
            "role": "SUPERADMIN",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if not superadmin.password:
        User.objects.filter(pk=superadmin.pk).update(
            password=make_password("SuperAdmin@123")
        )

    agent, _ = User.objects.get_or_create(
        username="agent_rajshahi",
        defaults={
            "email": "agent.rajshahi@farmhub.bd",
            "first_name": "Rajshahi",
            "last_name": "Agent",
            "role": "AGENT",
            "is_staff": True,
        },
    )
    if not agent.password:
        User.objects.filter(pk=agent.pk).update(password=make_password("Agent@123"))

    farm, _ = Farm.objects.get_or_create(
        name="Padma Dairy Farm",
        defaults={
            "location": "Rajshahi, Bangladesh",
            "agent_id": agent.id,
        },
    )
    if farm.agent_id != agent.id:
        farm.agent_id = agent.id
        farm.save()

    farmer_user, _ = User.objects.get_or_create(
        username="farmer_sunamganj",
        defaults={
            "email": "farmer.sunamganj@farmhub.bd",
            "first_name": "Abdul",
            "last_name": "Karim",
            "role": "FARMER",
        },
    )
    if not farmer_user.password:
        User.objects.filter(pk=farmer_user.pk).update(
            password=make_password("Farmer@123")
        )

    farmer_profile, _ = FarmerProfile.objects.get_or_create(
        user_id=farmer_user.id, defaults={"farm_id": farm.id}
    )
    if farmer_profile.farm_id != farm.id:
        farmer_profile.farm_id = farm.id
        farmer_profile.save()

    cow1, _ = Cow.objects.get_or_create(
        farm_id=farm.id,
        tag="BD-RJ-001",
        defaults={"breed": "Red Chittagong", "owner_id": farmer_profile.id},
    )
    if cow1.owner_id != farmer_profile.id:
        cow1.owner_id = farmer_profile.id
        cow1.save()

    cow2, _ = Cow.objects.get_or_create(
        farm_id=farm.id,
        tag="BD-RJ-002",
        defaults={"breed": "Sahiwal", "owner_id": farmer_profile.id},
    )
    if cow2.owner_id != farmer_profile.id:
        cow2.owner_id = farmer_profile.id
        cow2.save()

    today = timezone.now().date()
    yday = today - timedelta(days=1)

    Activity.objects.get_or_create(
        cow_id=cow1.id,
        type="vaccination",
        date=today,
        defaults={"notes": "FMD vaccine at Union Parishad clinic"},
    )
    Activity.objects.get_or_create(
        cow_id=cow2.id,
        type="health",
        date=today,
        defaults={"notes": "Routine health check by local vet"},
    )

    MilkRecord.objects.get_or_create(
        cow_id=cow1.id, date=yday, defaults={"liters": Decimal("7.50")}
    )
    MilkRecord.objects.get_or_create(
        cow_id=cow1.id, date=today, defaults={"liters": Decimal("7.80")}
    )
    MilkRecord.objects.get_or_create(
        cow_id=cow2.id, date=yday, defaults={"liters": Decimal("6.20")}
    )
    MilkRecord.objects.get_or_create(
        cow_id=cow2.id, date=today, defaults={"liters": Decimal("6.45")}
    )


def unseed_initial_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Farm = apps.get_model("farms", "Farm")
    FarmerProfile = apps.get_model("farms", "FarmerProfile")
    Cow = apps.get_model("livestock", "Cow")
    Activity = apps.get_model("livestock", "Activity")
    MilkRecord = apps.get_model("production", "MilkRecord")

    MilkRecord.objects.filter(cow__tag__in=["BD-RJ-001", "BD-RJ-002"]).delete()
    Activity.objects.filter(cow__tag__in=["BD-RJ-001", "BD-RJ-002"]).delete()
    Cow.objects.filter(tag__in=["BD-RJ-001", "BD-RJ-002"]).delete()
    FarmerProfile.objects.filter(user__username="farmer_sunamganj").delete()
    Farm.objects.filter(name="Padma Dairy Farm").delete()
    User.objects.filter(
        username__in=["farmer_sunamganj", "agent_rajshahi", "superadmin"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("farms", "0001_initial"),
        ("livestock", "0001_initial"),
        ("production", "0001_initial"),
    ]

    operations = [migrations.RunPython(seed_initial_data, unseed_initial_data)]
