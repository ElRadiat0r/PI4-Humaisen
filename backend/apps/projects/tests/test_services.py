
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.projects.choices import ProjectStatus as S
from apps.projects.models import Project
from apps.projects import services


class ProjectServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="client@example.com",
            password="test-password",
            role="CLIENT",
        )

        self.project = Project.objects.create(
            owner=self.user,
            title="Projet de test",
            description="Description suffisamment longue pour être valide.",
            consent_data_processing=True,
            consent_ai_analysis=False,
        )

    def test_valid_transition(self):
        """Une transition autorisée doit modifier le statut."""
        services.change_status(self.project, S.SUBMITTED)

        self.project.refresh_from_db()

        self.assertEqual(self.project.status, S.SUBMITTED)

    def test_invalid_transition(self):
        """Une transition non déclarée doit lever une exception."""
        with self.assertRaises(ValidationError):
            services.change_status(self.project, S.CLOSED)

    def test_transition_from_closed_is_impossible(self):
        """Un dossier clôturé ne peut plus changer de statut."""
        self.project.status = S.CLOSED
        self.project.save()

        with self.assertRaises(ValidationError):
            services.change_status(self.project, S.IN_PROGRESS)

    def test_submit_project(self):
        """Un dossier valide et avec consentement peut être soumis."""
        services.submit_project(self.project)

        self.project.refresh_from_db()

        self.assertEqual(self.project.status, S.SUBMITTED)

    def test_submit_without_data_processing_consent(self):
        """Le consentement au traitement des données est obligatoire."""
        self.project.consent_data_processing = False
        self.project.save()

        with self.assertRaises(ValidationError) as context:
            services.submit_project(self.project)

        self.assertIn(
            "consent_data_processing",
            context.exception.detail,
        )

    def test_submit_with_short_description(self):
        """Une description trop courte empêche la soumission."""
        self.project.description = "Trop court"
        self.project.save()

        with self.assertRaises(ValidationError) as context:
            services.submit_project(self.project)

        self.assertIn("description", context.exception.detail)

    def test_ai_consent_is_not_required_to_submit(self):
        """Le consentement IA reste facultatif."""
        self.project.consent_data_processing = True
        self.project.consent_ai_analysis = False
        self.project.save()

        services.submit_project(self.project)

        self.project.refresh_from_db()

        self.assertEqual(self.project.status, S.SUBMITTED)

    def test_cancel_project(self):
        """Un dossier brouillon peut être annulé."""
        services.cancel_project(self.project)

        self.project.refresh_from_db()

        self.assertEqual(self.project.status, S.CANCELLED)

    def test_cancel_closed_project(self):
        """Un dossier clôturé ne peut pas être annulé."""
        self.project.status = S.CLOSED
        self.project.save()

        with self.assertRaises(ValidationError):
            services.cancel_project(self.project)
