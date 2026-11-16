from django.urls import reverse
from rest_framework.test import APITestCase

from apps.experts.tests.factories import ExpertProfileFactory

from .factories import ProjectFactory, UserFactory


class ProjectPermissionTests(APITestCase):
    def setUp(self):
        self.owner = UserFactory(role="CLIENT")
        self.other = UserFactory(role="CLIENT")
        self.admin = UserFactory(role="ADMIN")
        self.expert = ExpertProfileFactory()
        self.project = ProjectFactory(owner=self.owner, assigned_expert=self.expert)
        self.detail = reverse("project-detail", args=[self.project.id])

    def test_anonymous_refused(self):
        self.assertIn(self.client.get(reverse("project-list")).status_code, (401, 403))

    def test_other_client_gets_404(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.detail).status_code, 404)

    def test_unassigned_humai_gets_404(self):
        self.client.force_authenticate(ExpertProfileFactory().user)
        self.assertEqual(self.client.get(self.detail).status_code, 404)

    def test_assigned_humai_cannot_modify(self):
        self.client.force_authenticate(self.expert.user)
        self.assertEqual(self.client.patch(self.detail, {"title": "x"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail).status_code, 403)

    def test_humai_cannot_create_project(self):
        self.client.force_authenticate(self.expert.user)
        resp = self.client.post(reverse("project-list"), {"title": "t", "description": "d" * 30}, format="json")
        self.assertEqual(resp.status_code, 403)

    def test_admin_cannot_submit_for_someone_else(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(reverse("project-submit", args=[self.project.id])).status_code, 403)

    def test_admin_can_delete_any(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(self.detail).status_code, 204)
