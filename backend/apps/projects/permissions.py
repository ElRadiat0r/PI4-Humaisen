from rest_framework.permissions import SAFE_METHODS, BasePermission

# À aligner avec les constantes de rôles fournies par P1 (accounts)
ROLE_CLIENT = "CLIENT"
ROLE_HUMAI = "HUMAI"
ROLE_ADMIN = "ADMIN"


def get_role(user):
    return getattr(user, "role", None)


def is_admin(user):
    return bool(user and user.is_authenticated and get_role(user) == ROLE_ADMIN)


def is_project_owner(user, project):
    return bool(user and user.is_authenticated and project.owner_id == user.id)


def is_assigned_expert(user, project):
    expert = project.assigned_expert
    return bool(
        expert is not None
        and user
        and user.is_authenticated
        and expert.user_id == user.id
    )


def can_view_project(user, project):
    return (
        is_admin(user)
        or is_project_owner(user, project)
        or is_assigned_expert(user, project)
    )


class IsClient(BasePermission):
    message = "Réservé aux clients."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and get_role(request.user) == ROLE_CLIENT
        )


class IsProjectOwner(BasePermission):
    message = "Vous n'êtes pas le propriétaire de ce dossier."

    def has_object_permission(self, request, view, obj):
        return is_project_owner(request.user, obj)


class IsOwnerOrAdmin(BasePermission):
    message = "Réservé au propriétaire du dossier ou à un administrateur."

    def has_object_permission(self, request, view, obj):
        return is_admin(request.user) or is_project_owner(request.user, obj)


class CanViewProject(BasePermission):
    """Lecture : propriétaire, HumAI assigné, admin. Écriture : propriétaire/admin."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return can_view_project(request.user, obj)
        return is_admin(request.user) or is_project_owner(request.user, obj)
