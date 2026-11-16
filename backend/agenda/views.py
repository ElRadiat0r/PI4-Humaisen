
from datetime import datetime

from django.db import IntegrityError, transaction

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AvailabilitySlot, Appointment
from .serializers import (
    AvailabilitySlotSerializer,
    AppointmentSerializer,
)


class AvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = AvailabilitySlot.objects.all()
        expert_id = self.request.query_params.get("expert_id")

        if expert_id:
            queryset = queryset.filter(expert_id=expert_id)

        return queryset

    @action(detail=True, methods=["post"])
    def block(self, request, pk=None):
        with transaction.atomic():
            slot = AvailabilitySlot.objects.select_for_update().get(
                pk=self.get_object().pk
            )

            if slot.appointments.filter(
                status=Appointment.Status.CONFIRMED
            ).exists():
                return Response(
                    {"error": "A booked slot cannot be blocked."},
                    status=status.HTTP_409_CONFLICT,
                )

            slot.is_available = False
            slot.save()

        return Response(self.get_serializer(slot).data)

    @action(detail=True, methods=["post"])
    def unblock(self, request, pk=None):
        slot = self.get_object()
        slot.is_available = True
        slot.save()

        return Response(self.get_serializer(slot).data)


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = Appointment.objects.select_related("slot")

        expert_id = self.request.query_params.get("expert_id")
        project_id = self.request.query_params.get("project_id")

        if expert_id:
            queryset = queryset.filter(expert_id=expert_id)

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        slot = serializer.validated_data["slot"]

        with transaction.atomic():
            locked_slot = AvailabilitySlot.objects.select_for_update().get(
                pk=slot.pk
            )

            if not locked_slot.is_available:
                return Response(
                    {"error": "This slot is unavailable."},
                    status=status.HTTP_409_CONFLICT,
                )

            if locked_slot.appointments.filter(
                status=Appointment.Status.CONFIRMED
            ).exists():
                return Response(
                    {"error": "This slot is already booked."},
                    status=status.HTTP_409_CONFLICT,
                )

            try:
                with transaction.atomic():
                    appointment = serializer.save()
            except IntegrityError:
                return Response(
                    {"error": "This slot has already been booked."},
                    status=status.HTTP_409_CONFLICT,
                )

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        appointment = self.get_object()

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {"error": "Only confirmed appointments can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointment.status = Appointment.Status.CANCELLED
        appointment.cancellation_reason = request.data.get("reason", "")
        appointment.save()

        return Response(self.get_serializer(appointment).data)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        new_slot_id = request.data.get("slot_id")

        if appointment.status != Appointment.Status.CONFIRMED:
            return Response(
                {"error": "Only confirmed appointments can be rescheduled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not new_slot_id:
            return Response(
                {"error": "slot_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                new_slot = AvailabilitySlot.objects.select_for_update().get(
                    pk=new_slot_id
                )

                if new_slot.expert_id != appointment.expert_id:
                    return Response(
                        {"error": "The new slot belongs to another expert."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not new_slot.is_available:
                    return Response(
                        {"error": "The new slot is unavailable."},
                        status=status.HTTP_409_CONFLICT,
                    )

                if new_slot.appointments.filter(
                    status=Appointment.Status.CONFIRMED
                ).exclude(pk=appointment.pk).exists():
                    return Response(
                        {"error": "The new slot is already booked."},
                        status=status.HTTP_409_CONFLICT,
                    )

                appointment.slot = new_slot
                appointment.save()

        except AvailabilitySlot.DoesNotExist:
            return Response(
                {"error": "Slot not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except IntegrityError:
            return Response(
                {"error": "The new slot has already been booked."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(self.get_serializer(appointment).data)


class MatchingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        required_skills = request.data.get("required_skills", [])
        requested_start = request.data.get("starts_at")
        requested_end = request.data.get("ends_at")
        candidates = request.data.get("candidates", [])

        if (
            not isinstance(required_skills, list)
            or not required_skills
            or not requested_start
            or not requested_end
            or not isinstance(candidates, list)
        ):
            return Response(
                {"error": "Invalid or missing matching parameters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start = datetime.fromisoformat(
                requested_start.replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(
                requested_end.replace("Z", "+00:00")
            )
        except (ValueError, TypeError, AttributeError):
            return Response(
                {"error": "Invalid date format. Use ISO 8601."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if end <= start:
            return Response(
                {"error": "ends_at must be after starts_at."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            candidate_skills = candidate.get("skills", [])

            if not isinstance(candidate_skills, list):
                continue

            try:
                expert_id = int(candidate["expert_id"])
                experience = max(
                    0, min(int(candidate.get("experience_years", 0)), 10)
                )
            except (KeyError, TypeError, ValueError):
                continue

            if not set(required_skills).issubset(set(candidate_skills)):
                continue

            available = AvailabilitySlot.objects.filter(
                expert_id=expert_id,
                is_available=True,
                starts_at__lte=start,
                ends_at__gte=end,
            ).exists()

            if not available:
                continue

            verified = candidate.get("is_verified", False)
            skills_score = 70
            verification_score = 20 if verified else 0
            experience_score = experience

            total_score = (
                skills_score + verification_score + experience_score
            )

            results.append({
                "expert_id": expert_id,
                "score": total_score,
                "justification": (
                    "All required skills match; availability confirmed; "
                    + (
                        "expert verified."
                        if verified
                        else "expert verification not confirmed."
                    )
                ),
            })

        results.sort(key=lambda item: item["score"], reverse=True)

        return Response({"results": results})
