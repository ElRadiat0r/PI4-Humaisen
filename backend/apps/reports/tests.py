from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.experts.models import ExpertProfile
from apps.projects.choices import ProjectStatus
from apps.projects.models import Project

from .models import Report


class ReportWorkflowTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.client_user = User.objects.create_user(email="client@example.com", password="TestPassword123!")
        self.humai_user = User.objects.create_user(email="humai@example.com", password="TestPassword123!", role="humai")
        self.other_humai = User.objects.create_user(email="other@example.com", password="TestPassword123!", role="humai")
        self.expert = ExpertProfile.objects.create(user=self.humai_user)
        ExpertProfile.objects.create(user=self.other_humai)
        self.project = Project.objects.create(
            owner=self.client_user,
            assigned_expert=self.expert,
            title="Projet de démonstration",
            description="Rénover un local professionnel et examiner les devis reçus.",
            status=ProjectStatus.IN_PROGRESS,
            consent_data_processing=True,
            consent_ai_analysis=True,
        )

    def create_draft(self):
        self.client.force_authenticate(self.humai_user)
        return self.client.post("/api/reports/", {"project": self.project.id}, format="json")

    def test_assigned_humai_can_create_draft(self):
        response = self.create_draft()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Report.Status.DRAFT)
        self.assertEqual(response.data["provider"], "synthetic-demo")
        self.assertEqual(Report.objects.count(), 1)

    def test_other_humai_cannot_create_report(self):
        self.client.force_authenticate(self.other_humai)

        response = self.client.post("/api/reports/", {"project": self.project.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Report.objects.count(), 0)

    def test_ai_generation_requires_both_consents(self):
        self.project.consent_ai_analysis = False
        self.project.save(update_fields=["consent_ai_analysis"])

        response = self.create_draft()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Report.objects.count(), 0)

    def test_client_cannot_read_draft_but_can_read_validated_report(self):
        created = self.create_draft()
        report_id = created.data["id"]

        self.client.force_authenticate(self.client_user)
        hidden = self.client.get(f"/api/reports/{report_id}/")
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.humai_user)
        validated = self.client.post(f"/api/reports/{report_id}/validate/", {}, format="json")
        self.assertEqual(validated.status_code, status.HTTP_200_OK)
        self.assertEqual(validated.data["status"], Report.Status.VALIDATED)

        self.client.force_authenticate(self.client_user)
        visible = self.client.get(f"/api/reports/{report_id}/")
        self.assertEqual(visible.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, ProjectStatus.DELIVERED)

    def test_validated_report_is_immutable(self):
        created = self.create_draft()
        report_id = created.data["id"]
        self.client.post(f"/api/reports/{report_id}/validate/", {}, format="json")

        response = self.client.patch(
            f"/api/reports/{report_id}/",
            {"content": {"overview": "Modified"}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
