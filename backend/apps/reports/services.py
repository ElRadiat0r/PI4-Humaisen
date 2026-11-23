from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.projects.choices import ProjectStatus
from apps.projects.models import Project
from apps.projects.permissions import is_assigned_expert
from apps.projects.services import change_status
from .models import Report
from .providers import AIProviderError, get_provider


def create_draft(project, user):
    if not is_assigned_expert(user, project):
        raise PermissionDenied("Seul l'HumAI affecté peut créer la restitution.")
    if not project.has_ai_consent:
        raise PermissionDenied("Les deux consentements requis doivent être actifs pour l'analyse IA.")
    provider = get_provider()
    try:
        content = provider.generate({"title": project.title, "description": project.description, "domain": project.get_domain_display()})
    except AIProviderError as exc:
        raise ValidationError({"ai_provider": str(exc)}) from exc
    if not isinstance(content, dict) or not content:
        raise ValidationError({"ai_provider": "Le fournisseur n'a pas retourné de contenu exploitable."})
    with transaction.atomic():
        locked_project = Project.objects.select_for_update().get(pk=project.pk)
        version = (locked_project.reports.order_by("-version").values_list("version", flat=True).first() or 0) + 1
        return Report.objects.create(project=locked_project, version=version, content=content, provider=provider.name, model_name=provider.model_name, created_by=user)


def validate_report(report, user):
    if not is_assigned_expert(user, report.project):
        raise PermissionDenied("Seul l'HumAI affecté peut valider cette restitution.")
    if report.status != Report.Status.DRAFT:
        raise ValidationError({"status": "Seul un brouillon peut être validé."})
    if not report.content or not report.content.get("overview"):
        raise ValidationError({"content": "Complétez la synthèse avant validation."})
    report.status = Report.Status.VALIDATED
    report.validated_by = user
    report.validated_at = timezone.now()
    report.save(update_fields=["status", "validated_by", "validated_at", "updated_at"])
    if report.project.status == ProjectStatus.IN_PROGRESS:
        change_status(report.project, ProjectStatus.DELIVERED)
    return report
