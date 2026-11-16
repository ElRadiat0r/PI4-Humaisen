
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AvailabilityViewSet,
    AppointmentViewSet,
    MatchingAPIView,
)

router = DefaultRouter()
router.register("availability", AvailabilityViewSet, basename="availability")
router.register("appointments", AppointmentViewSet, basename="appointments")

urlpatterns = [
    path("", include(router.urls)),
    path("matching/", MatchingAPIView.as_view(), name="matching"),
]
