from django.urls import reverse
from rest_framework.test import APITestCase

from apps.experts.choices import VerificationStatus
from apps.projects.tests.factories import UserFactory

from .factories import ExpertProfileFactory


class VerificationTests(APITestCase):
    def setUp(self):
        self.admin = UserFactory(role="ADMIN")
        self.profile = ExpertProfileFactory(verification_status=VerificationStatus.PENDING)

    def test_admin_can_verify(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(reverse("expert-verify", args=[self.profile.id]))
        self.assertEqual(resp.status_code, 200, resp.data)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.VERIFIED)
        self.assertEqual(self.profile.verified_by, self.admin)

    def test_verify_twice_fails(self):
        self.client.force_authenticate(self.admin)
        self.client.post(reverse("expert-verify", args=[self.profile.id]))
        self.assertEqual(self.client.post(reverse("expert-verify", args=[self.profile.id])).status_code, 400)

    def test_admin_can_reject_with_reason(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(reverse("expert-reject", args=[self.profile.id]), {"reason": "Pièces manquantes"})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.REJECTED)
        self.assertEqual(self.profile.rejection_reason, "Pièces manquantes")

    def test_client_and_humai_cannot_verify(self):
        for role in ("CLIENT", "HUMAI"):
            self.client.force_authenticate(UserFactory(role=role))
            resp = self.client.post(reverse("expert-verify", args=[self.profile.id]))
            self.assertIn(resp.status_code, (403, 404))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, VerificationStatus.PENDING)

    def test_expert_cannot_self_verify(self):
        self.client.force_authenticate(self.profile.user)
        resp = self.client.post(reverse("expert-verify", args=[self.profile.id]))
        self.assertEqual(resp.status_code, 403)
