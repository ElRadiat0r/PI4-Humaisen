from functools import lru_cache
from zoneinfo import available_timezones

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone as dj_timezone

from .choices import ExpertLevel, VerificationStatus


@lru_cache(maxsize=1)
def _timezones():
    return frozenset(available_timezones())


def validate_timezone(value):
    if value not in _timezones():
        raise ValidationError(f"Fuseau horaire invalide : {value}")


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ExpertProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expert_profile"
    )
    bio = models.TextField(blank=True)
    former_profession = models.CharField(max_length=150, blank=True)
    years_experience = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(70)]
    )
    level = models.PositiveSmallIntegerField(
        choices=ExpertLevel.choices, default=ExpertLevel.CONFIRMED
    )
    verification_status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    rejection_reason = models.TextField(blank=True)
    timezone = models.CharField(
        max_length=64, default="Europe/Paris", validators=[validate_timezone]
    )
    is_active = models.BooleanField(default=True)
    skills = models.ManyToManyField(Skill, through="ExpertSkill", related_name="experts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["verification_status", "is_active"])]

    def __str__(self):
        return f"HumAI #{self.pk} ({self.user})"

    @property
    def is_verified(self):
        return self.verification_status == VerificationStatus.VERIFIED

    def verify(self, admin_user=None):
        self.verification_status = VerificationStatus.VERIFIED
        self.verified_at = dj_timezone.now()
        self.verified_by = admin_user
        self.rejection_reason = ""
        self.save()

    def reject(self, reason="", admin_user=None):
        self.verification_status = VerificationStatus.REJECTED
        self.verified_at = None
        self.verified_by = admin_user
        self.rejection_reason = reason
        self.save()


class ExpertSkill(models.Model):
    expert = models.ForeignKey(
        ExpertProfile, on_delete=models.CASCADE, related_name="expert_skills"
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="expert_skills")
    level = models.PositiveSmallIntegerField(
        choices=ExpertLevel.choices, default=ExpertLevel.CONFIRMED
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["expert", "skill"], name="unique_expert_skill")
        ]

    def __str__(self):
        return f"{self.expert_id} – {self.skill}"
