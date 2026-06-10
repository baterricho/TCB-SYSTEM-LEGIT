import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import CustomUser, EvaluatorProfile
from applications.models import IPApplication
from cases.models import Case
from marketplace.models import IPRecord, MarketListing
from payments.models import FeeAssessment
from security_keys.services import EncryptionKeyService


TEST_MASTER_KEY = base64.urlsafe_b64encode(b"2" * 32).decode()


def create_user(email, role="applicant", password="StrongPass123!", **extra):
    defaults = {
        "first_name": extra.pop("first_name", "Test"),
        "last_name": extra.pop("last_name", "User"),
        "is_active": extra.pop("is_active", True),
    }
    defaults.update(extra)
    return CustomUser.objects.create_user(email=email, password=password, role=role, **defaults)


def create_case(applicant):
    application = IPApplication.objects.create(
        applicant=applicant,
        ip_type=IPApplication.IPType.PATENT,
        title="Endpoint contract invention",
        description="A test application for endpoint compatibility.",
        abstract="Endpoint compatibility abstract.",
        claims="A claim.",
        declaration_accepted=True,
        status=IPApplication.Status.SUBMITTED,
    )
    return Case.objects.create(application=application, applicant=applicant)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", MASTER_KEY=TEST_MASTER_KEY)
class EndpointContractsAndRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_token_refresh_contract_alias_works(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        admin = create_user("refresh-admin@example.com", role=CustomUser.Role.ADMIN, is_staff=True)
        refresh = str(RefreshToken.for_user(admin))

        refresh_response = self.client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")

        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)

    def test_evaluator_case_detail_and_status_alias_are_object_scoped(self):
        owner = create_user("case-owner@example.com")
        evaluator = create_user("case-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        other_evaluator = create_user("other-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        case = create_case(owner)
        case.taken_by = evaluator
        case.assigned_evaluator = evaluator
        case.is_taken = True
        case.status = Case.Status.UNDER_REVIEW
        case.save()

        self.client.force_authenticate(other_evaluator)
        denied = self.client.get(f"/api/cases/{case.id}/")
        self.assertEqual(denied.status_code, 404)

        self.client.force_authenticate(evaluator)
        updated = self.client.post(
            f"/api/cases/{case.id}/update-status/",
            {"status": Case.Status.EVALUATED, "remarks": "Completed evaluation."},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        case.refresh_from_db()
        self.assertEqual(case.status, Case.Status.EVALUATED)

    def test_applicant_submit_creates_available_case_for_matching_evaluator(self):
        applicant = create_user("submit-applicant@example.com")
        evaluator = create_user("available-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        EvaluatorProfile.objects.create(
            user=evaluator,
            specialization=EvaluatorProfile.Specialization.PATENT_MECHANICAL,
            is_available=True,
        )
        application = IPApplication.objects.create(
            applicant=applicant,
            ip_type=IPApplication.IPType.PATENT,
            title="Submitted workflow invention",
            description="A complete application description.",
            abstract="A complete abstract.",
            claims="A complete claim.",
            declaration_accepted=True,
        )

        self.client.force_authenticate(applicant)
        submit_response = self.client.post(f"/api/applications/{application.id}/submit/")

        self.assertEqual(submit_response.status_code, 201)
        application.refresh_from_db()
        self.assertEqual(application.status, IPApplication.Status.SUBMITTED)
        case = Case.objects.get(application=application)
        self.assertEqual(case.status, Case.Status.PENDING)
        self.assertFalse(case.is_taken)
        self.assertIsNone(case.taken_by)

        duplicate_response = self.client.post(f"/api/applications/{application.id}/submit/")
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertEqual(Case.objects.filter(application=application).count(), 1)

        self.client.force_authenticate(evaluator)
        available_response = self.client.get("/api/cases/available/")

        self.assertEqual(available_response.status_code, 200)
        available_cases = available_response.data["results"] if isinstance(available_response.data, dict) else available_response.data
        self.assertEqual(len(available_cases), 1)
        self.assertEqual(available_cases[0]["id"], case.id)
        self.assertEqual(available_cases[0]["application_code"], application.application_code)

    def test_taken_case_moves_from_available_to_evaluator_my_cases(self):
        applicant = create_user("take-applicant@example.com")
        evaluator = create_user("take-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        EvaluatorProfile.objects.create(
            user=evaluator,
            specialization=EvaluatorProfile.Specialization.PATENT_MECHANICAL,
            is_available=True,
        )
        case = create_case(applicant)

        self.client.force_authenticate(evaluator)
        take_response = self.client.post(f"/api/cases/{case.id}/take/")

        self.assertEqual(take_response.status_code, 200)
        case.refresh_from_db()
        self.assertTrue(case.is_taken)
        self.assertEqual(case.taken_by, evaluator)
        self.assertEqual(case.status, Case.Status.UNDER_REVIEW)
        self.assertIsNotNone(case.deadline)

        available_response = self.client.get("/api/cases/available/")
        available_cases = available_response.data["results"] if isinstance(available_response.data, dict) else available_response.data
        self.assertEqual(available_cases, [])

        my_cases_response = self.client.get("/api/cases/my-cases/")
        my_cases = my_cases_response.data["results"] if isinstance(my_cases_response.data, dict) else my_cases_response.data
        self.assertEqual(len(my_cases), 1)
        self.assertEqual(my_cases[0]["id"], case.id)

    def test_available_cases_backfills_submitted_applications_without_case(self):
        applicant = create_user("backfill-applicant@example.com")
        evaluator = create_user("backfill-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        EvaluatorProfile.objects.create(
            user=evaluator,
            specialization=EvaluatorProfile.Specialization.PATENT_MECHANICAL,
            is_available=True,
        )
        application = IPApplication.objects.create(
            applicant=applicant,
            ip_type=IPApplication.IPType.PATENT,
            title="Previously submitted invention",
            description="This was submitted before a case row existed.",
            abstract="Backfill abstract.",
            claims="Backfill claim.",
            declaration_accepted=True,
            status=IPApplication.Status.SUBMITTED,
        )
        self.assertFalse(Case.objects.filter(application=application).exists())

        self.client.force_authenticate(evaluator)
        response = self.client.get("/api/cases/available/")

        self.assertEqual(response.status_code, 200)
        case = Case.objects.get(application=application)
        self.assertEqual(case.status, Case.Status.PENDING)
        self.assertFalse(case.is_taken)
        self.assertIsNone(case.taken_by)
        available_cases = response.data["results"] if isinstance(response.data, dict) else response.data
        self.assertEqual(len(available_cases), 1)
        self.assertEqual(available_cases[0]["id"], case.id)

    def test_messages_contract_alias_saves_messages_for_case_participants(self):
        applicant = create_user("message-applicant@example.com")
        evaluator = create_user("message-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        case = create_case(applicant)
        case.taken_by = evaluator
        case.assigned_evaluator = evaluator
        case.is_taken = True
        case.save()

        self.client.force_authenticate(applicant)
        conversation = self.client.post("/api/messages/conversations/", {"case": case.id}, format="json")
        self.assertEqual(conversation.status_code, 201)

        evaluator_scoped = self.client.get("/api/evaluator/conversations/")
        self.assertEqual(evaluator_scoped.status_code, 403)

        message = self.client.post(
            f"/api/messages/conversations/{conversation.data['id']}/messages/",
            {"content": "Hello evaluator."},
            format="json",
        )
        self.assertEqual(message.status_code, 201)
        self.assertEqual(message.data["content"], "Hello evaluator.")

    def test_marketplace_bookmark_alias_and_admin_listing_permissions(self):
        admin = create_user("market-admin@example.com", role=CustomUser.Role.ADMIN, is_staff=True)
        applicant = create_user("market-applicant@example.com")
        case = create_case(applicant)
        record = IPRecord.objects.create(case=case, application=case.application, is_certified=True)
        listing = MarketListing.objects.create(
            record=record,
            admin=admin,
            title="Published listing",
            ip_type="Patent",
            inventor_name="Inventor",
            short_description="Short",
            full_description="Full",
            category="Technology",
            availability_status="Available",
            status=MarketListing.Status.PUBLISHED,
            is_active=True,
        )

        self.client.force_authenticate(applicant)
        bookmark = self.client.post(f"/api/marketplace/listings/{listing.id}/bookmark/")
        self.assertEqual(bookmark.status_code, 201)
        forbidden_admin_list = self.client.get("/api/marketplace/admin/listings/")
        self.assertEqual(forbidden_admin_list.status_code, 403)

        unbookmark = self.client.delete(f"/api/marketplace/listings/{listing.id}/bookmark/")
        self.assertEqual(unbookmark.status_code, 204)

    def test_non_admin_cannot_delete_public_announcement_or_listing(self):
        from announcements.models import Announcement

        admin = create_user("delete-admin@example.com", role=CustomUser.Role.ADMIN, is_staff=True)
        applicant = create_user("delete-applicant@example.com")
        announcement = Announcement.objects.create(
            admin=admin,
            title="Public notice",
            content="Public content",
            category="News",
            is_published=True,
        )
        case = create_case(applicant)
        record = IPRecord.objects.create(case=case, application=case.application, is_certified=True)
        listing = MarketListing.objects.create(
            record=record,
            admin=admin,
            title="Protected listing",
            ip_type="Patent",
            inventor_name="Inventor",
            short_description="Short",
            full_description="Full",
            category="Technology",
            availability_status="Available",
            status=MarketListing.Status.PUBLISHED,
            is_active=True,
        )

        self.client.force_authenticate(applicant)
        self.assertEqual(self.client.delete(f"/api/announcements/{announcement.id}/").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/marketplace/listings/{listing.id}/").status_code, 403)

    def test_payment_receipt_rejects_doc_files(self):
        admin = create_user("payment-admin@example.com", role=CustomUser.Role.ADMIN, is_staff=True)
        applicant = create_user("payment-applicant@example.com")
        EncryptionKeyService.generate_key(user=admin, key_name="Primary")
        case = create_case(applicant)
        assessment = FeeAssessment.objects.create(
            case=case,
            application=case.application,
            amount="100.00",
            fee_type="Filing",
            status=FeeAssessment.Status.ISSUED,
        )
        upload = SimpleUploadedFile("receipt.doc", b"not allowed", content_type="application/msword")

        self.client.force_authenticate(applicant)
        response = self.client.post(
            "/api/payments/",
            {
                "assessment": assessment.id,
                "amount_paid": "100.00",
                "payment_method": "Bank",
                "file": upload,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file type", str(response.data))
