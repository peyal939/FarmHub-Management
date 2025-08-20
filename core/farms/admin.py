from django.contrib import admin
from .models import Farm, FarmerProfile


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "agent")
    list_filter = ("agent",)
    search_fields = ("name", "location")


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "farm")
    list_filter = ("farm",)
    search_fields = ("user__username", "farm__name")
