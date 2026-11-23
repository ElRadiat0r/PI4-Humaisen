from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)

    class Meta:
        model = Report
        fields = ["id", "project", "project_title", "version", "status", "content", "provider", "model_name", "created_by", "validated_by", "created_at", "updated_at", "validated_at"]
        read_only_fields = ["id", "project", "project_title", "version", "status", "provider", "model_name", "created_by", "validated_by", "created_at", "updated_at", "validated_at"]

    def validate_content(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Le contenu doit être un objet JSON.")
        return value
