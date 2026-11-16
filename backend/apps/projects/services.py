"""Règles métier du cycle de vie d'un Dossier Projet.

P3 et P5 doivent passer par `change_status` pour modifier le statut
(matching, prise de rendez-vous, restitution...).
"""
from rest_framework.exceptions import ValidationError

from .choices import ProjectStatus as S

ALLOWED_TRANSITIONS = {
    S.DRAFT: {S.SUBMITTED, S.CANCELLED},
    S.SUBMITTED: {S.MATCHED, S.CANCELLED},
    S.MATCHED: {S.SCHEDULED, S.SUBMITTED, S.CANCELLED},
    S.SCHEDULED: {S.IN_PROGRESS, S.MATCHED, S.CANCELLED},
    S.IN_PROGRESS: {S.DELIVERED, S.CANCELLED},
    S.DELIVERED: {S.CLOSED, S.IN_PROGRESS},
    S.CLOSED: set(),
    S.CANCELLED: set(),
}

# Statuts dans lesquels le propriétaire peut modifier / supprimer son dossier
EDITABLE_STATUSES = {S.DRAFT}
DELETABLE_STATUSES = {S.DRAFT, S.CANCELLED}
FROZEN_STATUSES = {S.CLOSED, S.CANCELLED}  # plus de pièces jointes

MIN_DESCRIPTION_LENGTH = 20


def can_transition(current: str, new: str) -> bool:
    return new in ALLOWED_TRANSITIONS.get(current, set())


def change_status(project, new_status: str, *, save: bool = True):
    if not can_transition(project.status, new_status):
        raise ValidationError(
            {"status": f"Transition impossible : {project.status} → {new_status}."}
        )
    project.status = new_status
    if save:
        project.save(update_fields=["status", "updated_at"])
    return project


def submit_project(project):
    """DRAFT → SUBMITTED, après vérification des prérequis."""
    errors = {}
    if len(project.description.strip()) < MIN_DESCRIPTION_LENGTH:
        errors["description"] = (
            f"La description doit contenir au moins {MIN_DESCRIPTION_LENGTH} caractères."
        )
    if not project.consent_data_processing:
        errors["consent_data_processing"] = (
            "Le consentement au traitement des données est obligatoire pour soumettre."
        )
    if errors:
        raise ValidationError(errors)
    return change_status(project, S.SUBMITTED)


def cancel_project(project):
    return change_status(project, S.CANCELLED)
