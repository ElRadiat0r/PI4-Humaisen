from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .choices import VerificationStatus
from .filters import ExpertFilter
from .models import ExpertProfile, Skill
from .permissions import (
    ROLE_ADMIN, ROLE_HUMAI, IsAdminOrReadOnly, IsAdminRole, IsHumAI, get_role,
)
from .serializers import (
    ExpertDetailSerializer, ExpertListSerializer, ExpertUpdateSerializer, SkillSerializer,
)


class ExpertViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ExpertFilter
    search_fields = ["former_profession", "bio", "user__first_name", "user__last_name", "skills__name"]
    ordering_fields = ["level", "years_experience", "created_at"]

    def get_queryset(self):
        qs = ExpertProfile.objects.select_related("user").prefetch_related("expert_skills__skill")
        user = self.request.user
        role = get_role(user)
        if role == ROLE_ADMIN:
            return qs
        visible = Q(verification_status=VerificationStatus.VERIFIED, is_active=True)
        if role == ROLE_HUMAI:
            visible |= Q(user=user)  # un HumAI voit toujours son propre profil
        return qs.filter(visible)

    def get_serializer_class(self):
        if self.action == "list":
            return ExpertListSerializer
        if self.action == "me" and self.request.method == "PATCH":
            return ExpertUpdateSerializer
        return ExpertDetailSerializer

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated, IsHumAI])
    def me(self, request):
        profile, _ = ExpertProfile.objects.get_or_create(user=request.user)
        context = self.get_serializer_context()
        if request.method == "GET":
            return Response(ExpertDetailSerializer(profile, context=context).data)
        serializer = ExpertUpdateSerializer(profile, data=request.data, partial=True, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminRole])
    def verify(self, request, pk=None):
        profile = self.get_object()
        if profile.is_verified:
            raise ValidationError({"verification_status": "Ce profil est déjà vérifié."})
        profile.verify(request.user)
        return Response(ExpertDetailSerializer(profile, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdminRole])
    def reject(self, request, pk=None):
        profile = self.get_object()
        if profile.verification_status == VerificationStatus.REJECTED:
            raise ValidationError({"verification_status": "Ce profil est déjà refusé."})
        profile.reject(request.data.get("reason", ""), request.user)
        return Response(ExpertDetailSerializer(profile, context=self.get_serializer_context()).data)


class SkillViewSet(viewsets.ModelViewSet):
    """Lecture pour tout utilisateur connecté, écriture réservée aux admins."""

    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "category"]
