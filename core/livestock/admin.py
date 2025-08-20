from django.contrib import admin
from .models import Cow, Activity
from production.models import MilkRecord


class ActivityInline(admin.TabularInline):
    model = Activity
    extra = 0


class MilkRecordInline(admin.TabularInline):
    model = MilkRecord
    extra = 0


@admin.register(Cow)
class CowAdmin(admin.ModelAdmin):
    list_display = ("tag", "breed", "farm", "owner")
    list_filter = ("farm", "owner", "breed")
    search_fields = ("tag", "breed", "owner__user__username", "farm__name")
    list_select_related = ("farm", "owner", "owner__user")
    inlines = [ActivityInline, MilkRecordInline]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("cow", "type", "date")
    list_filter = ("type", "date")
    search_fields = ("cow__tag", "notes")
    list_select_related = ("cow",)
    date_hierarchy = "date"
