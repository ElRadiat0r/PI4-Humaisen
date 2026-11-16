from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.experts.tests.factories import ExpertProfileFactory
from apps.projects.choices import ProjectStatus as S

from .factories import ProjectFactory, UserFactory

PAYLOAD = {
    "title": "Optimiser ma trésorerie",
    "description": "Je cherche un avis d'expert sur la gestion de ma trésorerie.",
    "domain": "FINANCE",
    "consent_data_processing": True,
    "consent_ai_analysis": True,
}


def results(resp):
    return resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data


class ProjectCrudTests(APITestCase):
    def setUp(self):
        self.owner = UserFactory(role="CLIENT")
        self.other = UserFactory(role="CLIENT")
        self.admin = UserFactory(role="ADMIN")

    def test_create_sets_owner_and_draft(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.post(reverse("project-list"), {**PAYLOAD, "owner": self.other.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["owner"], self.owner.id)
        self.assertEqual(resp.data["status"], S.DRAFT)
        self.assertIsNotNone(resp.data["consent_date"])

    def test_status_cannot_be_set_on_create(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.post(reverse("project-list"), {**PAYLOAD, "status": "CLOSED"}, format="json")
        self.assertEqual(resp.data["status"], S.DRAFT)

    def test_ai_consent_requires_data_consent(self):
        self.client.force_authenticate(self.owner)
        bad = {**PAYLOAD, "consent_data_processing": False}
        resp = self.client.post(reverse("project-list"), bad, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_is_scoped_to_owner(self):
        ProjectFactory.create_batch(2, owner=self.owner)
        ProjectFactory(owner=self.other)
        self.client.force_authenticate(self.owner)
        self.assertEqual(len(results(self.client.get(reverse("project-list")))), 2)

    def test_admin_sees_all(self):
        ProjectFactory.create_batch(2, owner=self.owner)
        ProjectFactory(owner=self.other)
        self.client.force_authenticate(self.admin)
        self.assertEqual(len(results(self.client.get(reverse("project-list")))), 3)

    def test_filter_by_status(self):
        ProjectFactory(owner=self.owner, status=S.SUBMITTED)
        ProjectFactory(owner=self.owner)
        self.client.force_authenticate(self.owner)
        resp = self.client.get(reverse("project-list"), {"status": "SUBMITTED"})
        self.assertEqual(len(results(resp)), 1)

    def test_update_draft(self):
        p = ProjectFactory(owner=self.owner)
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(reverse("project-detail", args=[p.id]), {"title": "Nouveau titre"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["title"], "Nouveau titre")

    def test_update_forbidden_after_submission(self):
        p = ProjectFactory(owner=self.owner, status=S.SUBMITTED)
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(reverse("project-detail", args=[p.id]), {"title": "X"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_delete_draft(self):
        p = ProjectFactory(owner=self.owner)
        self.client.force_authenticate(self.owner)
        resp = self.client.delete(reverse("project-detail", args=[p.id]))
        self.assertEqual(resp.status_code, 204)

    def test_delete_submitted_refused_for_owner(self):
        p = ProjectFactory(owner=self.owner, status=S.SUBMITTED)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(reverse("project-detail", args=[p.id])).status_code, 400)

    def test_submit(self):
        p = ProjectFactory(owner=self.owner)
        self.client.force_authenticate(self.owner)
        resp = self.client.post(reverse("project-submit", args=[p.id]))
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], S.SUBMITTED)

    def test_submit_without_consent_fails(self):
        p = ProjectFactory(owner=self.owner, consent_data_processing=False, consent_ai_analysis=False)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(reverse("project-submit", args=[p.id])).status_code, 400)

    def test_submit_twice_fails(self):
        p = ProjectFactory(owner=self.owner, status=S.SUBMITTED)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(reverse("project-submit", args=[p.id])).status_code, 400)

    def test_cancel(self):
        p = ProjectFactory(owner=self.owner, status=S.SUBMITTED)
        self.client.force_authenticate(self.owner)
        resp = self.client.post(reverse("project-cancel", args=[p.id]))
        self.assertEqual(resp.data["status"], S.CANCELLED)

    def test_assigned_humai_can_read(self):
        expert = ExpertProfileFactory()
        p = ProjectFactory(owner=self.owner, assigned_expert=expert)
        self.client.force_authenticate(expert.user)
        self.assertEqual(self.client.get(reverse("project-detail", args=[p.id])).status_code, 200)
