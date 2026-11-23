from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("project", "version", "status", "provider", "created_by", "validated_by", "created_at")
    list_filter = ("status", "provider")
    readonly_fields = ("created_at", "updated_at", "validated_at")
