from django.db import models


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    VERIFIED = "VERIFIED", "Vérifié"
    REJECTED = "REJECTED", "Refusé"


class ExpertLevel(models.IntegerChoices):
    """Entier pour faciliter le score pondéré du matching (P3)."""

    CONFIRMED = 1, "Confirmé"
    SENIOR = 2, "Senior"
    EXPERT = 3, "Expert"
