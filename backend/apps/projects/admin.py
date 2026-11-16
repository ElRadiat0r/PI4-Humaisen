from django.contrib import admin

from .models import Project, ProjectAttachment


class AttachmentInline(admin.TabularInline):
    model = ProjectAttachment
    extra = 0
    readonly_fields = ["original_name", "size", "uploaded_at"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "owner", "domain", "status", "assigned_expert", "created_at"]
    list_filter = ["status", "domain"]
    search_fields = ["title", "description", "owner__email"]
    inlines = [AttachmentInline]
