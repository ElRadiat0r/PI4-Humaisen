
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase
from rest_framework import status

from .models import AvailabilitySlot, Appointment


class AgendaAPITests(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="agenda_test",
            password="TestPassword123!"
        )
        self.client.force_authenticate(user=self.user)

        self.start = timezone.now() + timedelta(days=3)
        self.end = self.start + timedelta(hours=1)

        self.slot = AvailabilitySlot.objects.create(
            expert_id=1,
            starts_at=self.start,
            ends_at=self.end,
            is_available=True,
        )

    def create_appointment(self, slot=None):
        return self.client.post(
            "/api/appointments/",
            {
                "project_id": 10,
                "expert_id": 1,
                "consultation_id": 5,
                "slot": (slot or self.slot).id,
            },
            format="json",
        )

    def test_list_availability(self):
        response = self.client.get("/api/availability/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_block_availability(self):
        response = self.client.post(
            f"/api/availability/{self.slot.id}/block/"
        )

        self.slot.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.slot.is_available)

    def test_create_appointment(self):
        response = self.create_appointment()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_prevent_double_booking(self):
        first_response = self.create_appointment()
        second_response = self.create_appointment()

        self.assertEqual(
            first_response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            second_response.status_code,
            status.HTTP_409_CONFLICT
        )
        self.assertEqual(Appointment.objects.count(), 1)

    def test_cancel_appointment(self):
        response = self.create_appointment()
        appointment_id = response.data["id"]

        cancel_response = self.client.post(
            f"/api/appointments/{appointment_id}/cancel/",
            {"reason": "Test cancellation"},
            format="json",
        )

        self.assertEqual(
            cancel_response.status_code,
            status.HTTP_200_OK
        )

        appointment = Appointment.objects.get(id=appointment_id)
        self.assertEqual(
            appointment.status,
            Appointment.Status.CANCELLED
        )

    def test_reschedule_appointment(self):
        response = self.create_appointment()
        appointment_id = response.data["id"]

        new_slot = AvailabilitySlot.objects.create(
            expert_id=1,
            starts_at=self.start + timedelta(days=1),
            ends_at=self.end + timedelta(days=1),
            is_available=True,
        )

        reschedule_response = self.client.post(
            f"/api/appointments/{appointment_id}/reschedule/",
            {"slot_id": new_slot.id},
            format="json",
        )

        self.assertEqual(
            reschedule_response.status_code,
            status.HTTP_200_OK
        )

        appointment = Appointment.objects.get(id=appointment_id)
        self.assertEqual(appointment.slot_id, new_slot.id)

    def test_matching_returns_available_expert(self):
        response = self.client.post(
            "/api/matching/",
            {
                "required_skills": ["Python", "Django"],
                "starts_at": self.start.isoformat(),
                "ends_at": self.end.isoformat(),
                "candidates": [
                    {
                        "expert_id": 1,
                        "skills": ["Python", "Django", "SQL"],
                        "is_verified": True,
                        "experience_years": 5,
                    },
                    {
                        "expert_id": 2,
                        "skills": ["Python"],
                        "is_verified": True,
                        "experience_years": 3,
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["expert_id"], 1)
