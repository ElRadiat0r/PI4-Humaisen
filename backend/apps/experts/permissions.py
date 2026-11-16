from rest_framework.permissions import SAFE_METHODS, BasePermission

# À aligner avec les constantes de rôles de P1 (accounts)
ROLE_HUMAI = "HUMAI"
ROLE_ADMIN = "ADMIN"


def get_role(user):
    return getattr(user, "role", None)


class IsHumAI(BasePermission):
    message = "Réservé aux experts HumAI."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and get_role(request.user) == ROLE_HUMAI)


class IsAdminRole(BasePermission):
    message = "Réservé aux administrateurs."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and get_role(request.user) == ROLE_ADMIN)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return get_role(request.user) == ROLE_ADMIN


class IsExpertOwner(BasePermission):
    """Objet : le profil appartient à l'utilisateur connecté."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
