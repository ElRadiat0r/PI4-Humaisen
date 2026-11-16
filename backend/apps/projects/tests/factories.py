import factory
from django.contrib.auth import get_user_model

from apps.projects.models import Project


class UserFactory(factory.django.DjangoModelFactory):
    """À adapter aux champs du modèle User de P1 (username/email/role)."""

    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    role = "CLIENT"
    password = factory.PostGenerationMethodCall("set_password", "Passw0rd!123")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    owner = factory.SubFactory(UserFactory, role="CLIENT")
    title = factory.Sequence(lambda n: f"Dossier {n}")
    description = "Description suffisamment longue pour passer la validation."
    domain = "IT"
    consent_data_processing = True
    consent_ai_analysis = True
