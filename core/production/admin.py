from django.contrib import admin
from .models import MilkRecord


@admin.register(MilkRecord)
class MilkRecordAdmin(admin.ModelAdmin):
    list_display = ("cow", "date", "liters")
    list_filter = ("date",)
    search_fields = ("cow__tag",)
    list_select_related = ("cow",)
    date_hierarchy = "date"
