import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.experts.tests.factories import ExpertProfileFactory
from apps.projects.choices import ProjectStatus as S
from apps.projects.models import ProjectAttachment
from apps.projects.validators import MAX_ATTACHMENT_SIZE, MAX_ATTACHMENTS_PER_PROJECT

from .factories import ProjectFactory, UserFactory


def pdf(name="note.pdf", content=b"%PDF-1.4 test"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class AttachmentTests(APITestCase):
    def setUp(self):
        self.owner = UserFactory(role="CLIENT")
        self.other = UserFactory(role="CLIENT")
        self.expert = ExpertProfileFactory()
        self.project = ProjectFactory(owner=self.owner, assigned_expert=self.expert)
        self.url = reverse("project-attachment-list", args=[self.project.id])

    def upload(self, f):
        return self.client.post(self.url, {"file": f}, format="multipart")

    def test_owner_can_upload(self):
        self.client.force_authenticate(self.owner)
        resp = self.upload(pdf())
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["original_name"], "note.pdf")
        self.assertEqual(ProjectAttachment.objects.count(), 1)

    def test_assigned_expert_can_upload_and_list(self):
        self.client.force_authenticate(self.expert.user)
        self.assertEqual(self.upload(pdf()).status_code, 201)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_bad_extension_refused(self):
        self.client.force_authenticate(self.owner)
        resp = self.upload(SimpleUploadedFile("virus.exe", b"MZ"))
        self.assertEqual(resp.status_code, 400)

    def test_too_large_refused(self):
        self.client.force_authenticate(self.owner)
        resp = self.upload(pdf(content=b"0" * (MAX_ATTACHMENT_SIZE + 1)))
        self.assertEqual(resp.status_code, 400)

    def test_max_count(self):
        self.client.force_authenticate(self.owner)
        for i in range(MAX_ATTACHMENTS_PER_PROJECT):
            self.assertEqual(self.upload(pdf(f"f{i}.pdf")).status_code, 201)
        self.assertEqual(self.upload(pdf("extra.pdf")).status_code, 400)

    def test_other_client_cannot_see_or_upload(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.upload(pdf()).status_code, 404)

    def test_closed_project_refuses_upload(self):
        self.project.status = S.CLOSED
        self.project.save()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.upload(pdf()).status_code, 400)

    def test_owner_can_delete(self):
        self.client.force_authenticate(self.owner)
        aid = self.upload(pdf()).data["id"]
        resp = self.client.delete(reverse("project-attachment-detail", args=[self.project.id, aid]))
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(ProjectAttachment.objects.count(), 0)

    def test_expert_cannot_delete(self):
        self.client.force_authenticate(self.owner)
        aid = self.upload(pdf()).data["id"]
        self.client.force_authenticate(self.expert.user)
        resp = self.client.delete(reverse("project-attachment-detail", args=[self.project.id, aid]))
        self.assertEqual(resp.status_code, 403)
