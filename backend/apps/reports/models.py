from django.conf import settings
from django.db import models


class Report(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        VALIDATED = "VALIDATED", "Validée par HumAI"

    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="reports")
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    content = models.JSONField(default=dict)
    provider = models.CharField(max_length=40, default="demo")
    model_name = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_reports")
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="validated_reports")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version"]
        constraints = [models.UniqueConstraint(fields=["project", "version"], name="unique_project_report_version")]

    def __str__(self):
        return f"Restitution {self.project_id} v{self.version} ({self.status})"
