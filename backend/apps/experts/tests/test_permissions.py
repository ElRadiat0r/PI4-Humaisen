from django.urls import reverse
from rest_framework.test import APITestCase

from apps.projects.tests.factories import UserFactory

from .factories import ExpertProfileFactory, SkillFactory


class ExpertPermissionTests(APITestCase):
    def test_anonymous_refused(self):
        for name in ("expert-list", "skill-list", "expert-me"):
            self.assertIn(self.client.get(reverse(name)).status_code, (401, 403))

    def test_skills_readable_by_any_authenticated_user(self):
        SkillFactory()
        self.client.force_authenticate(UserFactory(role="CLIENT"))
        self.assertEqual(self.client.get(reverse("skill-list")).status_code, 200)

    def test_skills_write_admin_only(self):
        self.client.force_authenticate(UserFactory(role="HUMAI"))
        self.assertEqual(self.client.post(reverse("skill-list"), {"name": "Nouveau"}).status_code, 403)
        self.client.force_authenticate(UserFactory(role="ADMIN"))
        self.assertEqual(self.client.post(reverse("skill-list"), {"name": "Nouveau"}).status_code, 201)

    def test_expert_endpoints_are_read_only(self):
        p = ExpertProfileFactory()
        self.client.force_authenticate(UserFactory(role="ADMIN"))
        self.assertEqual(self.client.delete(reverse("expert-detail", args=[p.id])).status_code, 405)
        self.assertEqual(self.client.post(reverse("expert-list"), {}).status_code, 405)
