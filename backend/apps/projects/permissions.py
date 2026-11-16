
from rest_framework.permissions import SAFE_METHODS, BasePermission


# À remplacer par les constantes communes de P1
ROLE_CLIENT = "CLIENT"
ROLE_HUMAI = "HUMAI"
ROLE_ADMIN = "ADMIN"


def get_role(user):
    if not user or not user.is_authenticated:
        return None

    return getattr(user, "role", None)


def is_admin(user):
    return get_role(user) == ROLE_ADMIN


def is_client(user):
    return get_role(user) == ROLE_CLIENT


def is_humai(user):
    return get_role(user) == ROLE_HUMAI


def is_project_owner(user, project):
    return bool(
        user
        and user.is_authenticated
        and project.owner_id == user.id
    )


def is_assigned_expert(user, project):
    return bool(
        user
        and user.is_authenticated
        and project.assigned_expert_id is not None
        and project.assigned_expert.user_id == user.id
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
        return is_client(request.user)


class IsAdmin(BasePermission):
    message = "Réservé aux administrateurs."

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsProjectOwner(BasePermission):
    message = "Vous n'êtes pas le propriétaire de ce dossier."

    def has_object_permission(self, request, view, obj):
        return is_project_owner(request.user, obj)


class IsOwnerOrAdmin(BasePermission):
    message = "Réservé au propriétaire du dossier ou à un administrateur."

    def has_object_permission(self, request, view, obj):
        return (
            is_admin(request.user)
            or is_project_owner(request.user, obj)
        )


class CanViewProject(BasePermission):
    """
    Lecture : propriétaire, HumAI assigné ou administrateur.
    Écriture : propriétaire ou administrateur.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return can_view_project(request.user, obj)

        return (
            is_admin(request.user)
            or is_project_owner(request.user, obj)
        )
