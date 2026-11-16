from django.db import transaction
from rest_framework import serializers

from .choices import ExpertLevel
from .models import ExpertProfile, ExpertSkill, Skill
from .permissions import ROLE_ADMIN, get_role


def display_name(user):
    return (user.get_full_name() or "").strip() or user.get_username()


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "category"]


class ExpertSkillReadSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)

    class Meta:
        model = ExpertSkill
        fields = ["skill", "level"]


class ExpertSkillWriteSerializer(serializers.Serializer):
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all())
    level = serializers.ChoiceField(choices=ExpertLevel.choices, default=ExpertLevel.CONFIRMED)


class ExpertListSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    level_label = serializers.CharField(source="get_level_display", read_only=True)
    skills = ExpertSkillReadSerializer(source="expert_skills", many=True, read_only=True)

    class Meta:
        model = ExpertProfile
        fields = [
            "id", "display_name", "former_profession", "level", "level_label",
            "timezone", "verification_status", "skills",
        ]
        read_only_fields = fields

    def get_display_name(self, obj):
        return display_name(obj.user)


class ExpertDetailSerializer(ExpertListSerializer):
    class Meta(ExpertListSerializer.Meta):
        fields = ExpertListSerializer.Meta.fields + [
            "bio", "years_experience", "is_active", "rejection_reason", "created_at",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        # le motif de refus n'est visible que par l'intéressé et les admins
        if not (user and (get_role(user) == ROLE_ADMIN or instance.user_id == user.id)):
            data.pop("rejection_reason", None)
        return data


class ExpertUpdateSerializer(serializers.ModelSerializer):
    skills = ExpertSkillWriteSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = ExpertProfile
        fields = [
            "bio", "former_profession", "years_experience", "level",
            "timezone", "is_active", "skills",
        ]

    def validate_skills(self, value):
        ids = [item["skill"].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Une compétence ne peut apparaître qu'une fois.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        skills = validated_data.pop("skills", None)
        instance = super().update(instance, validated_data)
        if skills is not None:
            instance.expert_skills.all().delete()
            ExpertSkill.objects.bulk_create(
                ExpertSkill(expert=instance, skill=item["skill"], level=item["level"])
                for item in skills
            )
        return instance

    def to_representation(self, instance):
        return ExpertDetailSerializer(instance, context=self.context).data
