from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.experts.choices import VerificationStatus
from apps.projects.tests.factories import UserFactory

from .factories import ExpertProfileFactory, ExpertSkillFactory, SkillFactory


class ExpertModelTests(TestCase):
    def test_default_status_pending(self):
        p = ExpertProfileFactory(verification_status=VerificationStatus.PENDING)
        self.assertFalse(p.is_verified)

    def test_unique_expert_skill(self):
        link = ExpertSkillFactory()
        with self.assertRaises(IntegrityError), transaction.atomic():
            ExpertSkillFactory(expert=link.expert, skill=link.skill)

    def test_invalid_timezone(self):
        p = ExpertProfileFactory.build(timezone="Mars/Olympus", user=UserFactory(role="HUMAI"))
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_verify_and_reject(self):
        admin = UserFactory(role="ADMIN")
        p = ExpertProfileFactory(verification_status=VerificationStatus.PENDING)
        p.verify(admin)
        p.refresh_from_db()
        self.assertTrue(p.is_verified)
        self.assertIsNotNone(p.verified_at)
        p.reject("Dossier incomplet", admin)
        p.refresh_from_db()
        self.assertEqual(p.verification_status, VerificationStatus.REJECTED)
        self.assertEqual(p.rejection_reason, "Dossier incomplet")

    def test_skill_name_unique(self):
        SkillFactory(name="Python")
        with self.assertRaises(IntegrityError), transaction.atomic():
            SkillFactory(name="Python")
