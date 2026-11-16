
from django.db import models
from django.db.models import Q


class AvailabilitySlot(models.Model):
    expert_id = models.PositiveIntegerField(db_index=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__gt=models.F("starts_at")),
                name="slot_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["expert_id", "starts_at", "ends_at"],
                name="unique_expert_time_slot",
            ),
        ]

    def __str__(self):
        return f"Expert {self.expert_id}: {self.starts_at}"


class Appointment(models.Model):

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    project_id = models.PositiveIntegerField(db_index=True)
    expert_id = models.PositiveIntegerField(db_index=True)
    consultation_id = models.PositiveIntegerField()

    slot = models.ForeignKey(
        AvailabilitySlot,
        on_delete=models.PROTECT,
        related_name="appointments",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )

    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["slot"],
                condition=Q(status="confirmed"),
                name="one_confirmed_appointment_per_slot",
            )
        ]

    def __str__(self):
        return f"Appointment {self.id} - {self.status}"
