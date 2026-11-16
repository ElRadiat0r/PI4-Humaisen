"""Données de démonstration SYNTHÉTIQUES (aucune donnée réelle).

Usage : python manage.py seed_experts --count 10
Idempotent : relancer la commande ne crée pas de doublons.
"""
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.experts.choices import ExpertLevel, VerificationStatus
from apps.experts.models import ExpertProfile, ExpertSkill, Skill

SKILLS = {
    "Finance": ["Gestion de trésorerie", "Analyse financière", "Levée de fonds"],
    "Juridique": ["Droit des sociétés", "Propriété intellectuelle", "Droit du travail"],
    "Informatique": ["Architecture logicielle", "Cybersécurité", "Gestion de projet IT"],
    "RH": ["Recrutement", "Gestion des talents"],
    "Management": ["Stratégie d'entreprise", "Conduite du changement"],
    "Industrie": ["Qualité / ISO", "Supply chain"],
}
FIRST = ["Alain", "Brigitte", "Claude", "Denise", "Étienne", "Françoise", "Gérard", "Hélène", "Jacques", "Monique"]
LAST = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau"]
PROFESSIONS = [
    "Ancien directeur financier", "Ancienne juriste d'entreprise", "Ancien DSI",
    "Ancienne DRH", "Ancien directeur d'usine", "Ancienne consultante en stratégie",
]
TIMEZONES = ["Europe/Paris", "Europe/Paris", "Europe/Paris", "Europe/Brussels", "Africa/Dakar"]


class Command(BaseCommand):
    help = "Crée des skills et des profils HumAI de démonstration."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10)
        parser.add_argument("--password", default="Demo1234!")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(42)  # reproductible
        User = get_user_model()

        skills = []
        for category, names in SKILLS.items():
            for name in names:
                skill, _ = Skill.objects.get_or_create(name=name, defaults={"category": category})
                skills.append(skill)

        created = 0
        for i in range(options["count"]):
            username = f"demo_expert_{i + 1}"
            user, new = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": FIRST[i % len(FIRST)],
                    "last_name": LAST[(i * 3) % len(LAST)],
                    "role": "HUMAI",
                },
            )
            if new:
                user.set_password(options["password"])
                user.save()
                created += 1

            profile, _ = ExpertProfile.objects.get_or_create(
                user=user,
                defaults={
                    "bio": "Profil de démonstration généré automatiquement.",
                    "former_profession": PROFESSIONS[i % len(PROFESSIONS)],
                    "years_experience": rng.randint(15, 40),
                    "level": rng.choice(list(ExpertLevel.values)),
                    "timezone": rng.choice(TIMEZONES),
                    # ~ 80 % vérifiés, 1 sur 5 en attente pour tester l'interface admin
                    "verification_status": (
                        VerificationStatus.PENDING if i % 5 == 4 else VerificationStatus.VERIFIED
                    ),
                },
            )
            if not profile.expert_skills.exists():
                for skill in rng.sample(skills, k=rng.randint(2, 4)):
                    ExpertSkill.objects.create(
                        expert=profile, skill=skill, level=rng.choice(list(ExpertLevel.values))
                    )

        self.stdout.write(self.style.SUCCESS(
            f"{created} nouveaux comptes HumAI ({options['count']} profils au total)."
        ))
