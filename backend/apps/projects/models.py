
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .choices import ProjectDomain, ProjectStatus
from .validators import validate_attachment, validate_consents


def attachment_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"projects/{instance.project_id}/{uuid.uuid4().hex}{ext}"


class Project(models.Model):
    """Dossier Projet créé par un Client."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    assigned_expert = models.ForeignKey(
        "experts.ExpertProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_projects",
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    domain = models.CharField(
        max_length=30,
        choices=ProjectDomain.choices,
        default=ProjectDomain.OTHER,
    )

    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT,
    )

    consent_data_processing = models.BooleanField(default=False)
    consent_ai_analysis = models.BooleanField(default=False)
    consent_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self):
        return f"#{self.pk} {self.title}"

    @property
    def has_ai_consent(self):
        return (
            self.consent_data_processing
            and self.consent_ai_analysis
        )

    def clean(self):
        super().clean()

        validate_consents(
            self.consent_data_processing,
            self.consent_ai_analysis,
        )


class ProjectAttachment(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    file = models.FileField(
        upload_to=attachment_upload_path,
        validators=[validate_attachment],
    )

    original_name = models.CharField(max_length=255)

    size = models.PositiveIntegerField(
        editable=False,
        help_text="Taille en octets",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size

        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name
