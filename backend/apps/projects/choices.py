from django.db import models


class ProjectStatus(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    SUBMITTED = "SUBMITTED", "Soumis"
    MATCHED = "MATCHED", "Expert trouvé"
    SCHEDULED = "SCHEDULED", "Consultation planifiée"
    IN_PROGRESS = "IN_PROGRESS", "En cours"
    DELIVERED = "DELIVERED", "Restitution livrée"
    CLOSED = "CLOSED", "Clôturé"
    CANCELLED = "CANCELLED", "Annulé"


class ProjectDomain(models.TextChoices):
    FINANCE = "FINANCE", "Finance / Comptabilité"
    LEGAL = "LEGAL", "Juridique"
    IT = "IT", "Informatique / Digital"
    HR = "HR", "Ressources humaines"
    MARKETING = "MARKETING", "Marketing / Vente"
    INDUSTRY = "INDUSTRY", "Industrie / Production"
    MANAGEMENT = "MANAGEMENT", "Management / Stratégie"
    OTHER = "OTHER", "Autre"
