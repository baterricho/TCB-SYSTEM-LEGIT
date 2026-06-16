import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from accounts.models import CustomUser
from applications.models import IPApplication
from auditlog.models import AuditLog
from cases.models import Case
from documents.services import DocumentService
from security_keys.services import EncryptionKeyService


TEST_MASTER_KEY = base64.urlsafe_b64encode(b"1" * 32).decode()


def create_user(email, role="applicant", password="StrongPass123!", **extra):
    defaults = {
        "first_name": extra.pop("first_name", "Test"),
        "last_name": extra.pop("last_name", "User"),
        "is_active": extra.pop("is_active", True),
    }
    defaults.update(extra)
    return CustomUser.objects.create_user(email=email, password=password, role=role, **defaults)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    MASTER_KEY=TEST_MASTER_KEY,
    REST_FRAMEWORK={"DEFAULT_THROTTLE_CLASSES": [], "DEFAULT_THROTTLE_RATES": {}}
)
class SystemAuditFixTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_public_inquiry_create_does_not_raise_audit_attribute_error(self):
        response = self.client.post(
            "/api/inquiries/",
            {
                "sender_name": "Public User",
                "email": "public@example.com",
                "category": "General",
                "subject": "Licensing question",
                "message": "How can I inquire about a marketplace listing?",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["inquiry_code"].startswith("INQ-"))
        self.assertTrue(AuditLog.objects.filter(action="inquiry.created", record_id=response.data["inquiry_code"]).exists())

    def test_search_endpoints_use_real_model_fields(self):
        admin = create_user("admin-search@example.com", role=CustomUser.Role.ADMIN, is_staff=True)
        self.client.force_authenticate(admin)

        for url in ("/api/audit-logs/?search=created", "/api/security-keys/?search=primary"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

        self.client.force_authenticate(user=None)
        response = self.client.get("/api/marketplace/listings/?search=innovation")
        self.assertEqual(response.status_code, 200)

    def test_evaluator_cannot_upload_document_to_unassigned_case(self):
        applicant = create_user("document-owner@example.com")
        evaluator = create_user("document-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        admin = create_user("document-admin@example.com", role=CustomUser.Role.ADMIN, is_staff=True)
        EncryptionKeyService.generate_key(user=admin, key_name="Primary")
        application = IPApplication.objects.create(
            applicant=applicant,
            ip_type=IPApplication.IPType.PATENT,
            title="Secure document workflow",
            description="A test application for document authorization.",
            declaration_accepted=True,
        )
        case = Case.objects.create(application=application, applicant=applicant)
        upload = SimpleUploadedFile("evidence.pdf", b"%PDF-1.4\nprivate content", content_type="application/pdf")

        with self.assertRaises(PermissionDenied):
            DocumentService.upload(
                uploaded_file=upload,
                uploaded_by=evaluator,
                document_type="supporting_document",
                case=case,
            )
