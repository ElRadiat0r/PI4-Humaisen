from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import AttachmentViewSet, ProjectViewSet

router = SimpleRouter()
router.register("projects", ProjectViewSet, basename="project")

attachment_list = AttachmentViewSet.as_view({"get": "list", "post": "create"})
attachment_detail = AttachmentViewSet.as_view({"delete": "destroy"})

urlpatterns = [
    path("projects/<int:project_pk>/attachments/", attachment_list, name="project-attachment-list"),
    path(
        "projects/<int:project_pk>/attachments/<int:pk>/",
        attachment_detail,
        name="project-attachment-detail",
    ),
] + router.urls
