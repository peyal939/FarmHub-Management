from django.contrib import admin
from .models import Cow, Activity


@admin.register(Cow)
class CowAdmin(admin.ModelAdmin):
	list_display = ("tag", "breed", "farm", "owner")
	list_filter = ("farm", "owner", "breed")
	search_fields = ("tag", "breed", "owner__user__username", "farm__name")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
	list_display = ("cow", "type", "date")
	list_filter = ("type", "date")
	search_fields = ("cow__tag", "notes")
