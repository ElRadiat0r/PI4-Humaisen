
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.projects.choices import ProjectStatus as S
from apps.projects.models import Project, ProjectAttachment


User = get_user_model()


class ProjectAPITests(APITestCase):

    def create_user(self, email, role):
        return User.objects.create_user(
            email=email,
            password="test-password",
            role=role,
        )

    def setUp(self):
        self.client_user = self.create_user(
            "client@example.com",
            "CLIENT",
        )

        self.other_client = self.create_user(
            "other@example.com",
            "CLIENT",
        )

        self.humai_user = self.create_user(
            "humai@example.com",
            "HUMAI",
        )

        self.admin_user = self.create_user(
            "admin@example.com",
            "ADMIN",
        )

        self.project = Project.objects.create(
            owner=self.client_user,
            title="Projet de test",
            description="Description suffisamment longue pour être valide.",
            consent_data_processing=True,
            consent_ai_analysis=False,
        )

        self.project_list_url = reverse("project-list")
        self.project_detail_url = reverse(
            "project-detail",
            kwargs={"pk": self.project.pk},
        )
        self.project_submit_url = reverse(
            "project-submit",
            kwargs={"pk": self.project.pk},
        )
        self.project_cancel_url = reverse(
            "project-cancel",
            kwargs={"pk": self.project.pk},
        )

    def test_unauthenticated_user_cannot_list_projects(self):
        response = self.client.get(self.project_list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_client_can_create_project(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.post(
            self.project_list_url,
            {
                "title": "Nouveau projet",
                "description": "Description détaillée du nouveau projet.",
                "domain": "IT",
                "consent_data_processing": True,
                "consent_ai_analysis": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 2)

        created_project = Project.objects.get(title="Nouveau projet")
        self.assertEqual(created_project.owner, self.client_user)

    def test_humai_cannot_create_project(self):
        self.client.force_authenticate(user=self.humai_user)

        response = self.client.post(
            self.project_list_url,
            {
                "title": "Projet interdit",
                "description": "Description détaillée du projet.",
                "domain": "IT",
                "consent_data_processing": True,
                "consent_ai_analysis": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_can_only_see_own_projects(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.get(self.project_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_other_client_cannot_retrieve_project(self):
        self.client.force_authenticate(user=self.other_client)

        response = self.client.get(self.project_detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_retrieve_project(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.get(self.project_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.project.pk)

    def test_owner_can_update_draft_project(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.patch(
            self.project_detail_url,
            {"title": "Titre modifié"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Titre modifié")

    def test_owner_cannot_update_submitted_project(self):
        self.project.status = S.SUBMITTED
        self.project.save()

        self.client.force_authenticate(user=self.client_user)

        response = self.client.patch(
            self.project_detail_url,
            {"title": "Modification interdite"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_submit_project(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.post(self.project_submit_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, S.SUBMITTED)

    def test_owner_cannot_submit_without_consent(self):
        self.project.consent_data_processing = False
        self.project.save()

        self.client.force_authenticate(user=self.client_user)

        response = self.client.post(self.project_submit_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, S.DRAFT)

    def test_owner_can_cancel_project(self):
        self.client.force_authenticate(user=self.client_user)

        response = self.client.post(self.project_cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.project.refresh_from_db()
        self.assertEqual(self.project.status, S.CANCELLED)

    def test_admin_can_retrieve_project(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.project_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProjectAttachmentAPITests(APITestCase):

    def create_user(self, email, role):
        return User.objects.create_user(
            email=email,
            password="test-password",
            role=role,
        )

    def setUp(self):
        self.client_user = self.create_user(
            "client@example.com",
            "CLIENT",
        )

        self.other_client = self.create_user(
            "other@example.com",
            "CLIENT",
        )

        self.project = Project.objects.create(
            owner=self.client_user,
            title="Projet avec fichier",
            description="Description suffisamment longue pour être valide.",
            consent_data_processing=True,
        )

        self.attachment_list_url = reverse(
            "project-attachment-list",
            kwargs={"project_pk": self.project.pk},
        )

    def test_owner_can_upload_attachment(self):
        self.client.force_authenticate(user=self.client_user)

        uploaded_file = SimpleUploadedFile(
            "document.txt",
            b"Contenu du document de test.",
            content_type="text/plain",
        )

        response = self.client.post(
            self.attachment_list_url,
            {"file": uploaded_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ProjectAttachment.objects.filter(project=self.project).count(),
            1,
        )

    def test_other_client_cannot_list_attachments(self):
        self.client.force_authenticate(user=self.other_client)

        response = self.client.get(self.attachment_list_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_cannot_upload_more_than_ten_attachments(self):
        for index in range(10):
            ProjectAttachment.objects.create(
                project=self.project,
                file=SimpleUploadedFile(
                    f"document_{index}.txt",
                    b"Contenu de test.",
                    content_type="text/plain",
                ),
                original_name=f"document_{index}.txt",
                size=len(b"Contenu de test."),
            )

        self.client.force_authenticate(user=self.client_user)

        uploaded_file = SimpleUploadedFile(
            "eleventh.txt",
            b"Contenu du onzieme document.",
            content_type="text/plain",
        )

        response = self.client.post(
            self.attachment_list_url,
            {"file": uploaded_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            ProjectAttachment.objects.filter(project=self.project).count(),
            10,
        )
