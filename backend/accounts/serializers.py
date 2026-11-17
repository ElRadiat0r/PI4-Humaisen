
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    role = serializers.ChoiceField(
        choices=[
            (User.Role.CLIENT, "Client"),
            (User.Role.HUMAI, "HumAI"),
        ],
        default=User.Role.CLIENT
    )

    class Meta:
        model = User
        fields = ["id", "email", "password", "role"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data["role"]
        )
