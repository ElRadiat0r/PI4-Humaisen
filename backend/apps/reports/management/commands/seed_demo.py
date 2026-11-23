"""Crée un scénario de démonstration avec des comptes et contenus synthétiques."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.experts.choices import VerificationStatus
from apps.experts.models import ExpertProfile
from apps.projects.choices import ProjectDomain, ProjectStatus
from apps.projects.models import Project
from apps.reports.models import Report
from apps.reports.providers import DemoProvider


class Command(BaseCommand):
    help = "Crée un dossier HUMAISEN de démonstration et son brouillon synthétique."

    def handle(self, *args, **options):
        User = get_user_model()
        client, _ = User.objects.get_or_create(
            email="demo.client@humaisen.test",
            defaults={"role": "client", "first_name": "Camille", "last_name": "Démo"},
        )
        client.set_password("Demo1234!")
        client.save(update_fields=["password"])
        humai, _ = User.objects.get_or_create(
            email="demo.humai@humaisen.test",
            defaults={"role": "humai", "first_name": "Alex", "last_name": "Démo"},
        )
        humai.set_password("Demo1234!")
        humai.save(update_fields=["password"])
        expert, _ = ExpertProfile.objects.get_or_create(
            user=humai,
            defaults={"verification_status": VerificationStatus.VERIFIED},
        )
        if not expert.is_verified:
            expert.verification_status = VerificationStatus.VERIFIED
            expert.save(update_fields=["verification_status"])

        project, _ = Project.objects.get_or_create(
            owner=client,
            title="Dossier de rénovation — démonstration",
            defaults={
                "assigned_expert": expert,
                "description": "Comparer deux devis de rénovation d'un local professionnel et planifier les travaux.",
                "domain": ProjectDomain.INDUSTRY,
                "status": ProjectStatus.IN_PROGRESS,
                "consent_data_processing": True,
                "consent_ai_analysis": True,
            },
        )
        if project.assigned_expert_id != expert.id:
            project.assigned_expert = expert
            project.save(update_fields=["assigned_expert", "updated_at"])
        provider = DemoProvider()
        Report.objects.get_or_create(
            project=project,
            version=1,
            defaults={
                "content": provider.generate({
                    "title": project.title,
                    "description": project.description,
                    "domain": project.get_domain_display(),
                }),
                "provider": provider.name,
                "model_name": provider.model_name,
                "created_by": humai,
            },
        )

        self.stdout.write(self.style.SUCCESS(
            "Données synthétiques prêtes. Client: demo.client@humaisen.test / HumAI: "
            "demo.humai@humaisen.test — mot de passe: Demo1234!"
        ))
