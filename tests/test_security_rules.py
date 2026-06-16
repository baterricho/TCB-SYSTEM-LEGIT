import base64
import os
import re
import tempfile

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import CustomUser, OTPCode
from accounts.services import OTPService
from applications.models import IPApplication
from cases.models import Case
from documents.services import DocumentService
from security_keys.models import EncryptionKey
from security_keys.services import EncryptionKeyService


TEST_MASTER_KEY = base64.urlsafe_b64encode(b"0" * 32).decode()


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
class SecurityRulesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        from unittest.mock import patch
        from rest_framework.throttling import SimpleRateThrottle
        self.patcher = patch.dict(SimpleRateThrottle.THROTTLE_RATES, {
            "auth": "10000/min",
            "otp": "10000/min",
            "registration": "10000/min",
            "password_reset": "10000/min",
        })
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_otp_is_hashed_expires_and_does_not_accept_random_code(self):
        user = create_user("otp@example.com")
        otp = OTPService.create_and_send(user, OTPCode.Purpose.LOGIN)
        otp.refresh_from_db()
        self.assertNotRegex(otp.otp_hash, r"^\d{6}$")

        with self.assertRaisesMessage(Exception, "Invalid OTP code. Please try again."):
            OTPService.verify(user, OTPCode.Purpose.LOGIN, "000000")

        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        OTPService.verify(user, OTPCode.Purpose.LOGIN, code)

        with self.assertRaisesMessage(Exception, "This OTP code has already been used."):
            OTPService.verify(user, OTPCode.Purpose.LOGIN, code)

    def test_login_locks_account_after_three_failed_attempts(self):
        user = create_user("lock@example.com", password="CorrectPass123!")
        url = "/api/auth/login/"
        for _ in range(3):
            response = self.client.post(url, {"email": user.email, "password": "WrongPass123!"}, format="json")
            self.assertEqual(response.status_code, 401)
        user.refresh_from_db()
        self.assertEqual(user.failed_login_attempts, 3)
        self.assertIsNotNone(user.locked_until)

    def test_applicant_cannot_retrieve_another_applicants_application(self):
        owner = create_user("owner@example.com")
        other = create_user("other@example.com")
        application = IPApplication.objects.create(
            applicant=owner,
            ip_type=IPApplication.IPType.PATENT,
            title="Secure hinge assembly",
            description="A mechanical hinge assembly for secure modular cabinets.",
            abstract="A cabinet hinge assembly.",
            claims="A secure hinge assembly comprising interlocking plates.",
            declaration_accepted=True,
        )
        self.client.force_authenticate(other)
        response = self.client.get(f"/api/applications/{application.id}/")
        self.assertEqual(response.status_code, 404)

    def test_only_taken_evaluator_can_update_case_status(self):
        applicant = create_user("applicant@example.com")
        evaluator = create_user("eval@example.com", role="evaluator")
        application = IPApplication.objects.create(
            applicant=applicant,
            ip_type=IPApplication.IPType.PATENT,
            title="Water purifier housing",
            description="A water purifier housing for field use.",
            abstract="A housing for water purification components.",
            claims="A purifier housing with sealed compartments.",
            declaration_accepted=True,
        )
        case = Case.objects.create(application=application, applicant=applicant)
        self.client.force_authenticate(evaluator)
        response = self.client.post(f"/api/cases/{case.id}/update-status/", {"status": Case.Status.EVALUATED}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Only the evaluator who took this case can update the case status.")

    def test_encryption_key_api_never_exposes_raw_material_and_documents_decrypt_for_owner(self):
        admin = create_user("admin@example.com", role="admin", is_staff=True)
        applicant = create_user("doc-owner@example.com")
        key = EncryptionKeyService.generate_key(user=admin, key_name="Primary Test Key")
        self.assertEqual(key.status, EncryptionKey.Status.ACTIVE)

        self.client.force_authenticate(admin)
        response = self.client.get("/api/security-keys/")
        self.assertEqual(response.status_code, 200)
        payload = response.data["results"][0] if isinstance(response.data, dict) and "results" in response.data else response.data[0]
        self.assertIn("masked_key_material", payload)
        self.assertNotIn("encrypted_key_material", payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(MEDIA_ROOT=tmpdir):
                application = IPApplication.objects.create(
                    applicant=applicant,
                    ip_type=IPApplication.IPType.COPYRIGHT,
                    title="Instructional module",
                    description="A written instructional module.",
                    declaration_accepted=True,
                )
                case = Case.objects.create(application=application, applicant=applicant)
                upload = SimpleUploadedFile("module.pdf", b"%PDF-1.4\nconfidential-ip-content", content_type="application/pdf")
                document = DocumentService.upload(
                    uploaded_file=upload,
                    uploaded_by=applicant,
                    document_type="supporting_document",
                    case=case,
                )
                with document.encrypted_file_path.open("rb") as encrypted_file:
                    self.assertNotEqual(encrypted_file.read(), b"%PDF-1.4\nconfidential-ip-content")
                self.assertEqual(DocumentService.decrypt(document, applicant), b"%PDF-1.4\nconfidential-ip-content")
