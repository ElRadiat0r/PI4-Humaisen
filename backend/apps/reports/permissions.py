from rest_framework.permissions import BasePermission
from apps.projects.permissions import is_assigned_expert, is_project_owner

ROLE_ADMIN = "admin"
ROLE_HUMAI = "humai"


def role_for(user):
    """Accepte les valeurs P1 minuscules et les anciennes constantes P2 majuscules."""
    return str(getattr(user, "role", "")).lower()


class ReportAccessPermission(BasePermission):
    """L'HumAI affecté gère les brouillons; le client voit les versions validées."""
    def has_object_permission(self, request, view, obj):
        role = role_for(request.user)
        if role == ROLE_ADMIN:
            return request.method in {"GET", "HEAD", "OPTIONS"}
        if role == ROLE_HUMAI:
            return is_assigned_expert(request.user, obj.project)
        return is_project_owner(request.user, obj.project) and obj.status == obj.Status.VALIDATED and request.method in {"GET", "HEAD", "OPTIONS"}
