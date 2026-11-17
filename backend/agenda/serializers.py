
from rest_framework import serializers
from .models import AvailabilitySlot, Appointment


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        start = data.get(
            "starts_at",
            getattr(self.instance, "starts_at", None)
        )
        end = data.get(
            "ends_at",
            getattr(self.instance, "ends_at", None)
        )

        if start and end and end <= start:
            raise serializers.ValidationError(
                "The end time must be after the start time."
            )

        return data



class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = "__all__"
        validators = []
        read_only_fields = [
            "status",
            "cancellation_reason",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):
        slot = data.get("slot")
        expert_id = data.get("expert_id")

        if slot:
            if not slot.is_available:
                raise serializers.ValidationError(
                    "This time slot is unavailable."
                )

            if expert_id != slot.expert_id:
                raise serializers.ValidationError(
                    "The selected slot does not belong to this expert."
                )

        return data
