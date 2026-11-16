from django.utils import timezone
from rest_framework import serializers

from .models import Project, ProjectAttachment
from .validators import validate_attachment, validate_consents


class AttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(validators=[validate_attachment])

    class Meta:
        model = ProjectAttachment
        fields = ["id", "project", "file", "original_name", "size", "uploaded_at"]
        read_only_fields = ["id", "project", "original_name", "size", "uploaded_at"]

    def create(self, validated_data):
        uploaded = validated_data["file"]
        validated_data["original_name"] = uploaded.name[:255]
        validated_data["size"] = uploaded.size
        return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    """Lecture d'un dossier."""

    attachments_count = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id", "owner", "assigned_expert", "title", "description", "domain",
            "status", "status_label", "consent_data_processing", "consent_ai_analysis",
            "consent_date", "attachments_count", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_attachments_count(self, obj):
        # valeur annotée par le queryset si disponible (évite un N+1)
        count = getattr(obj, "attachments_count", None)
        return count if count is not None else obj.attachments.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Création et modification (le statut et le propriétaire ne sont jamais écrits ici)."""

    class Meta:
        model = Project
        fields = [
            "title", "description", "domain",
            "consent_data_processing", "consent_ai_analysis",
        ]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le titre est obligatoire.")
        return value

    def validate_description(self, value):
        return value.strip()

    def validate(self, attrs):
        current = self.instance
        data = attrs.get(
            "consent_data_processing", getattr(current, "consent_data_processing", False)
        )
        ai = attrs.get(
            "consent_ai_analysis", getattr(current, "consent_ai_analysis", False)
        )
        try:
            validate_consents(data, ai)
        except Exception as exc:  # DjangoValidationError
            raise serializers.ValidationError({"consent_ai_analysis": list(exc.messages)})
        return attrs

    def update(self, instance, validated_data):
        before = (instance.consent_data_processing, instance.consent_ai_analysis)
        instance = super().update(instance, validated_data)
        after = (instance.consent_data_processing, instance.consent_ai_analysis)
        if before != after:  # on retrace la date du dernier changement de consentement
            instance.consent_date = timezone.now() if any(after) else None
            instance.save(update_fields=["consent_date", "updated_at"])
        return instance

    def to_representation(self, instance):
        return ProjectSerializer(instance, context=self.context).data
