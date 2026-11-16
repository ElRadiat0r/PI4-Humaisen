# Intégration – Personne 2 (apps `projects` et `experts`)

## 1. requirements.txt (ajouts)
```
django-filter
factory-boy
drf-spectacular   # optionnel, schéma OpenAPI
tzdata            # fuseaux horaires (Windows / images Docker minimales)
```

## 2. settings/base.py
```python
INSTALLED_APPS += [
    "django_filters",
    "apps.experts",
    "apps.projects",
]

REST_FRAMEWORK = {
    # ...config de P1 (auth, permissions par défaut)...
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

## 3. config/urls.py
```python
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    # ...
    path("api/", include("apps.experts.urls")),
    path("api/", include("apps.projects.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # dev uniquement
```

## 4. Contrat avec P1 (à valider)
- `settings.AUTH_USER_MODEL` possède un champ `role` ∈ {`CLIENT`, `HUMAI`, `ADMIN`}.
- `UserFactory` (projects/tests/factories.py) est à adapter aux champs réels de User.

## 5. Contrat avec P3 / P5
- `Project.assigned_expert` (FK → `ExpertProfile`) est à renseigner par P3 (matching / réservation).
- Changements de statut : toujours via `apps.projects.services.change_status(project, new_status)`.
- P5 : vérifier `project.has_ai_consent` avant tout envoi à l'IA.
- `ExpertProfile.level` est un entier (1-3), `ExpertSkill.level` aussi : utilisable directement dans le score.
- Données de démo : `python manage.py seed_experts --count 10`.

## 6. Commandes
```
python manage.py makemigrations experts projects
python manage.py migrate
python manage.py test apps.projects apps.experts
```
