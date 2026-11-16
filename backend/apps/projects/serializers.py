
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from rest_framework import serializers

from .models import Project, ProjectAttachment
from .validators import (
    validate_attachment,
    validate_consents,
    MAX_ATTACHMENTS_PER_PROJECT,
)


class AttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(validators=[validate_attachment])

    class Meta:
        model = ProjectAttachment
        fields = [
            "id",
            "project",
            "file",
            "original_name",
            "size",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "project",
            "original_name",
            "size",
            "uploaded_at",
        ]

    def validate(self, attrs):
        # Le projet doit être fourni par la vue, jamais librement
        # par le client via les données JSON.
        project = self.context.get("project")

        if project is None and self.instance:
            project = self.instance.project

        if project is not None and self.instance is None:
            if project.attachments.count() >= MAX_ATTACHMENTS_PER_PROJECT:
                raise serializers.ValidationError({
                    "file": "Maximum de 10 pièces jointes par projet."
                })

        return attrs

    def create(self, validated_data):
        uploaded = validated_data["file"]

        validated_data["original_name"] = uploaded.name[:255]
        validated_data["size"] = uploaded.size

        return super().create(validated_data)


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer de lecture d'un dossier."""

    attachments_count = serializers.SerializerMethodField()

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "owner",
            "assigned_expert",
            "title",
            "description",
            "domain",
            "status",
            "status_label",
            "consent_data_processing",
            "consent_ai_analysis",
            "consent_date",
            "attachments_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_attachments_count(self, obj):
        count = getattr(obj, "attachments_count", None)

        if count is not None:
            return count

        return obj.attachments.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Création et modification d'un dossier."""

    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "domain",
            "consent_data_processing",
            "consent_ai_analysis",
        ]

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Le titre est obligatoire."
            )

        return value

    def validate_description(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "La description est obligatoire."
            )

        return value

    def validate(self, attrs):
        current = self.instance

        data_processing = attrs.get(
            "consent_data_processing",
            getattr(current, "consent_data_processing", False),
        )

        ai_analysis = attrs.get(
            "consent_ai_analysis",
            getattr(current, "consent_ai_analysis", False),
        )

        try:
            validate_consents(data_processing, ai_analysis)

        except DjangoValidationError as exc:
            raise serializers.ValidationError({
                "consent_ai_analysis": exc.messages
            })

        return attrs

    def create(self, validated_data):
        if (
            validated_data.get("consent_data_processing", False)
            or validated_data.get("consent_ai_analysis", False)
        ):
            validated_data["consent_date"] = timezone.now()

        return super().create(validated_data)

    def update(self, instance, validated_data):
        before = (
            instance.consent_data_processing,
            instance.consent_ai_analysis,
        )

        after = (
            validated_data.get(
                "consent_data_processing",
                instance.consent_data_processing,
            ),
            validated_data.get(
                "consent_ai_analysis",
                instance.consent_ai_analysis,
            ),
        )

        if before != after:
            validated_data["consent_date"] = timezone.now()

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ProjectSerializer(
            instance,
            context=self.context,
        ).data
