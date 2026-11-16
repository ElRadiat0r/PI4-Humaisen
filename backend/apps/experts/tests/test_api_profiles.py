from django.urls import reverse
from rest_framework.test import APITestCase

from apps.experts.choices import VerificationStatus
from apps.projects.tests.factories import UserFactory

from .factories import ExpertProfileFactory, ExpertSkillFactory, SkillFactory


def results(resp):
    return resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data


class ExpertListTests(APITestCase):
    def setUp(self):
        self.client_user = UserFactory(role="CLIENT")
        self.verified = ExpertProfileFactory()
        self.pending = ExpertProfileFactory(verification_status=VerificationStatus.PENDING)
        self.inactive = ExpertProfileFactory(is_active=False)

    def test_client_sees_only_verified_active(self):
        self.client.force_authenticate(self.client_user)
        ids = [e["id"] for e in results(self.client.get(reverse("expert-list")))]
        self.assertEqual(ids, [self.verified.id])

    def test_client_cannot_open_pending_profile(self):
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.get(reverse("expert-detail", args=[self.pending.id])).status_code, 404)

    def test_admin_sees_everything(self):
        self.client.force_authenticate(UserFactory(role="ADMIN"))
        self.assertEqual(len(results(self.client.get(reverse("expert-list")))), 3)

    def test_humai_sees_own_pending_profile(self):
        self.client.force_authenticate(self.pending.user)
        self.assertEqual(self.client.get(reverse("expert-detail", args=[self.pending.id])).status_code, 200)

    def test_rejection_reason_hidden_from_clients(self):
        self.client.force_authenticate(self.client_user)
        resp = self.client.get(reverse("expert-detail", args=[self.verified.id]))
        self.assertNotIn("rejection_reason", resp.data)

    def test_filter_by_skill_and_level(self):
        link = ExpertSkillFactory(expert=self.verified)
        other = ExpertProfileFactory(level=1)
        self.client.force_authenticate(self.client_user)
        resp = self.client.get(reverse("expert-list"), {"skill": link.skill_id})
        self.assertEqual([e["id"] for e in results(resp)], [self.verified.id])
        resp = self.client.get(reverse("expert-list"), {"min_level": 2})
        self.assertNotIn(other.id, [e["id"] for e in results(resp)])


class ExpertMeTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role="HUMAI")
        self.url = reverse("expert-me")

    def test_get_creates_profile(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["verification_status"], VerificationStatus.PENDING)

    def test_patch_profile_and_skills(self):
        s1, s2 = SkillFactory(), SkillFactory()
        self.client.force_authenticate(self.user)
        payload = {
            "bio": "Trente ans d'expérience.",
            "timezone": "Europe/Brussels",
            "skills": [{"skill": s1.id, "level": 3}, {"skill": s2.id, "level": 1}],
        }
        resp = self.client.patch(self.url, payload, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["bio"], "Trente ans d'expérience.")
        self.assertEqual(len(resp.data["skills"]), 2)
        # remplacement complet de la liste
        resp = self.client.patch(self.url, {"skills": [{"skill": s1.id}]}, format="json")
        self.assertEqual(len(resp.data["skills"]), 1)

    def test_cannot_set_verification_status(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.url, {"verification_status": "VERIFIED"}, format="json")
        self.assertEqual(resp.data["verification_status"], VerificationStatus.PENDING)

    def test_invalid_timezone(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.url, {"timezone": "Mars/Olympus"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_skills_refused(self):
        s = SkillFactory()
        self.client.force_authenticate(self.user)
        resp = self.client.patch(self.url, {"skills": [{"skill": s.id}, {"skill": s.id}]}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_client_cannot_use_me(self):
        self.client.force_authenticate(UserFactory(role="CLIENT"))
        self.assertEqual(self.client.get(self.url).status_code, 403)
