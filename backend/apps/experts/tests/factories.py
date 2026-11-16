import factory

from apps.experts.choices import ExpertLevel, VerificationStatus
from apps.experts.models import ExpertProfile, ExpertSkill, Skill
from apps.projects.tests.factories import UserFactory


class SkillFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Skill

    name = factory.Sequence(lambda n: f"Compétence {n}")
    category = "Informatique"


class ExpertProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpertProfile

    user = factory.SubFactory(UserFactory, role="HUMAI")
    bio = "Bio de test"
    former_profession = "Ancien directeur"
    years_experience = 25
    level = ExpertLevel.SENIOR
    verification_status = VerificationStatus.VERIFIED
    timezone = "Europe/Paris"


class ExpertSkillFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpertSkill

    expert = factory.SubFactory(ExpertProfileFactory)
    skill = factory.SubFactory(SkillFactory)
    level = ExpertLevel.SENIOR
