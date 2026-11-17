from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentification
    path("api/auth/", include("accounts.urls")),

    # Agenda
    path("api/", include("agenda.urls")),
]

