from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.projects import services
from apps.projects.choices import ProjectStatus as S

from .factories import ProjectFactory


class ProjectModelTests(TestCase):
    def test_default_status_is_draft(self):
        self.assertEqual(ProjectFactory().status, S.DRAFT)

    def test_consent_date_set_when_consent_given(self):
        self.assertIsNotNone(ProjectFactory(consent_data_processing=True).consent_date)

    def test_no_consent_date_without_consent(self):
        p = ProjectFactory(consent_data_processing=False, consent_ai_analysis=False)
        self.assertIsNone(p.consent_date)

    def test_has_ai_consent_requires_both(self):
        p = ProjectFactory(consent_data_processing=True, consent_ai_analysis=False)
        self.assertFalse(p.has_ai_consent)
        p = ProjectFactory(consent_data_processing=True, consent_ai_analysis=True)
        self.assertTrue(p.has_ai_consent)


class StatusServiceTests(TestCase):
    def test_valid_transition(self):
        p = ProjectFactory()
        services.change_status(p, S.SUBMITTED)
        p.refresh_from_db()
        self.assertEqual(p.status, S.SUBMITTED)

    def test_invalid_transition(self):
        with self.assertRaises(ValidationError):
            services.change_status(ProjectFactory(), S.DELIVERED)

    def test_closed_is_final(self):
        p = ProjectFactory(status=S.CLOSED)
        with self.assertRaises(ValidationError):
            services.change_status(p, S.DRAFT)

    def test_submit_requires_consent(self):
        p = ProjectFactory(consent_data_processing=False, consent_ai_analysis=False)
        with self.assertRaises(ValidationError):
            services.submit_project(p)

    def test_submit_requires_description(self):
        with self.assertRaises(ValidationError):
            services.submit_project(ProjectFactory(description="court"))
