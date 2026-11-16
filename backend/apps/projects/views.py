from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .filters import ProjectFilter
from .models import Project, ProjectAttachment
from .permissions import (
    ROLE_ADMIN, ROLE_HUMAI, IsClient, IsOwnerOrAdmin, IsProjectOwner,
    can_view_project, get_role, is_admin, is_assigned_expert, is_project_owner,
)
from .serializers import AttachmentSerializer, ProjectCreateSerializer, ProjectSerializer
from .validators import MAX_ATTACHMENTS_PER_PROJECT


class ProjectViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "status"]

    def get_queryset(self):
        qs = Project.objects.select_related("owner", "assigned_expert__user").annotate(
            attachments_count=Count("attachments")
        )
        user = self.request.user
        role = get_role(user)
        if role == ROLE_ADMIN:
            return qs
        if role == ROLE_HUMAI:
            return qs.filter(assigned_expert__user=user)
        return qs.filter(owner=user)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProjectCreateSerializer
        return ProjectSerializer

    def get_permissions(self):
        if self.action == "create":
            classes = [IsAuthenticated, IsClient]
        elif self.action in ("update", "partial_update", "destroy"):
            classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action in ("submit", "cancel"):
            classes = [IsAuthenticated, IsProjectOwner]
        else:
            classes = [IsAuthenticated]
        return [cls() for cls in classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        project = serializer.instance
        if not is_admin(self.request.user) and project.status not in services.EDITABLE_STATUSES:
            raise ValidationError(
                {"status": "Un dossier ne peut être modifié qu'à l'état brouillon."}
            )
        serializer.save()

    def perform_destroy(self, instance):
        if not is_admin(self.request.user) and instance.status not in services.DELETABLE_STATUSES:
            raise ValidationError(
                {"status": "Seul un dossier brouillon ou annulé peut être supprimé."}
            )
        for attachment in instance.attachments.all():
            attachment.file.delete(save=False)
        instance.delete()

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        project = services.submit_project(self.get_object())
        return Response(ProjectSerializer(project, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        project = services.cancel_project(self.get_object())
        return Response(ProjectSerializer(project, context={"request": request}).data)



class AttachmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_project(self):
        if not hasattr(self, "_project"):
            project = get_object_or_404(
                Project.objects.select_related("assigned_expert__user"),
                pk=self.kwargs["project_pk"],
            )

            if not can_view_project(self.request.user, project):
                raise NotFound()

            self._project = project

        return self._project

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ProjectAttachment.objects.none()

        return ProjectAttachment.objects.filter(
            project=self.get_project()
        )

    def perform_create(self, serializer):
        project = self.get_project()
        user = self.request.user

        allowed = (
            is_admin(user)
            or is_project_owner(user, project)
            or is_assigned_expert(user, project)
        )

        if not allowed:
            raise PermissionDenied(
                "Vous ne pouvez pas ajouter de pièce jointe à ce dossier."
            )

        if project.status in services.FROZEN_STATUSES:
            raise ValidationError({
                "status": "Ce dossier est clos ou annulé."
            })

        if project.attachments.count() >= MAX_ATTACHMENTS_PER_PROJECT:
            raise ValidationError({
                "file": (
                    f"Maximum {MAX_ATTACHMENTS_PER_PROJECT} "
                    "pièces jointes par dossier."
                )
            })

        serializer.save(project=project)

    def perform_destroy(self, instance):
        user = self.request.user

        if not (
            is_admin(user)
            or is_project_owner(user, instance.project)
        ):
            raise PermissionDenied(
                "Seul le propriétaire ou l'administrateur "
                "peut supprimer une pièce jointe."
            )

        if instance.project.status in services.FROZEN_STATUSES:
            raise ValidationError({
                "status": "Impossible de supprimer un fichier de ce dossier."
            })

        instance.file.delete(save=False)
        instance.delete()

