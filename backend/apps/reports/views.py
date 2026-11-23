from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.projects.models import Project
from .models import Report
from .permissions import ROLE_ADMIN, ROLE_HUMAI, ReportAccessPermission, role_for
from apps.projects.permissions import is_assigned_expert
from .serializers import ReportSerializer
from .services import create_draft, validate_report


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, ReportAccessPermission]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        role = role_for(self.request.user)
        queryset = Report.objects.select_related("project", "project__owner", "project__assigned_expert__user")
        if role == ROLE_ADMIN:
            return queryset
        if role == ROLE_HUMAI:
            queryset = queryset.filter(project__assigned_expert__user=self.request.user)
        else:
            queryset = queryset.filter(project__owner=self.request.user, status=Report.Status.VALIDATED)
        project_id = self.request.query_params.get("project")
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def create(self, request, *args, **kwargs):
        if role_for(request.user) != ROLE_HUMAI:
            raise PermissionDenied("La création d'une restitution est réservée à l'HumAI affecté.")
        project = get_object_or_404(Project.objects.select_related("assigned_expert__user"), pk=request.data.get("project"))
        if not is_assigned_expert(request.user, project):
            raise PermissionDenied("Vous n'êtes pas affecté à ce dossier.")
        report = create_draft(project, request.user)
        return Response(self.get_serializer(report).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        report = serializer.instance
        if role_for(self.request.user) != ROLE_HUMAI or not is_assigned_expert(self.request.user, report.project):
            raise PermissionDenied("Seul l'HumAI affecté peut modifier le brouillon.")
        if report.status != Report.Status.DRAFT:
            raise ValidationError({"status": "Une restitution validée est en lecture seule. Créez une nouvelle version."})
        serializer.save()

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        report = validate_report(self.get_object(), request.user)
        return Response(self.get_serializer(report).data)
