from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import CustomUser
from applications.models import IPApplication
from auditlog.models import AuditLog
from cases.models import Case


TEST_MASTER_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="


def create_user(email, role=CustomUser.Role.APPLICANT, password="StrongPass123!", **extra):
    defaults = {
        "first_name": extra.pop("first_name", "Test"),
        "last_name": extra.pop("last_name", "User"),
        "is_active": extra.pop("is_active", True),
    }
    defaults.update(extra)
    return CustomUser.objects.create_user(email=email, password=password, role=role, **defaults)


def create_case(applicant, evaluator=None, title="Exportable invention", ip_type=IPApplication.IPType.PATENT, status=Case.Status.PENDING):
    application = IPApplication.objects.create(
        applicant=applicant,
        ip_type=ip_type,
        title=title,
        description="A real database record used for export tests.",
        abstract="Export abstract.",
        claims="Export claim.",
        declaration_accepted=True,
        status=IPApplication.Status.SUBMITTED,
        submitted_at=timezone.now(),
    )
    return Case.objects.create(
        application=application,
        applicant=applicant,
        assigned_evaluator=evaluator,
        taken_by=evaluator,
        is_taken=bool(evaluator),
        taken_at=timezone.now() if evaluator else None,
        status=status,
        deadline=timezone.now() + timezone.timedelta(days=3),
    )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", MASTER_KEY=TEST_MASTER_KEY)
class ReportExportTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_admin_portfolio_analytics_export_uses_real_records_and_audits(self):
        admin = create_user("portfolio-admin@example.com", role=CustomUser.Role.ADMIN, is_staff=True)
        applicant = create_user("portfolio-applicant@example.com", first_name="Real", last_name="Applicant")
        case = create_case(applicant, title="Solar dryer controller", status=Case.Status.UNDER_REVIEW)

        self.client.force_authenticate(admin)
        response = self.client.get("/api/reports/portfolio-analytics/export/?ip_service=Patent")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        payload = response.content.decode()
        self.assertIn("Portfolio Analytics Report", payload)
        self.assertIn(case.case_number, payload)
        self.assertIn(case.application.application_code, payload)
        self.assertIn("Solar dryer controller", payload)
        self.assertTrue(AuditLog.objects.filter(user=admin, action="reports.portfolio_analytics_exported").exists())

    def test_non_admin_cannot_export_portfolio_analytics(self):
        applicant = create_user("portfolio-denied@example.com")

        self.client.force_authenticate(applicant)
        response = self.client.get("/api/reports/portfolio-analytics/export/")

        self.assertEqual(response.status_code, 403)

    def test_evaluator_case_export_is_limited_to_assigned_or_taken_cases_and_audits(self):
        evaluator = create_user("export-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        other_evaluator = create_user("other-export-evaluator@example.com", role=CustomUser.Role.EVALUATOR)
        own_applicant = create_user("own-export-applicant@example.com")
        other_applicant = create_user("other-export-applicant@example.com")
        own_case = create_case(own_applicant, evaluator=evaluator, title="Authorized case", status=Case.Status.EVALUATED)
        other_case = create_case(other_applicant, evaluator=other_evaluator, title="Unauthorized case", status=Case.Status.EVALUATED)

        self.client.force_authenticate(evaluator)
        response = self.client.get("/api/evaluator/export/cases/")

        self.assertEqual(response.status_code, 200)
        payload = response.content.decode()
        self.assertIn("Evaluator Case Report", payload)
        self.assertIn(own_case.case_number, payload)
        self.assertIn("Authorized case", payload)
        self.assertNotIn(other_case.case_number, payload)
        self.assertNotIn("Unauthorized case", payload)
        self.assertTrue(AuditLog.objects.filter(user=evaluator, action="reports.evaluator_case_report_exported").exists())

    def test_evaluator_scope_override_is_blocked_and_audited(self):
        evaluator = create_user("blocked-export-evaluator@example.com", role=CustomUser.Role.EVALUATOR)

        self.client.force_authenticate(evaluator)
        response = self.client.get("/api/evaluator/export/cases/?assigned_evaluator_id=999")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(AuditLog.objects.filter(user=evaluator, action="reports.evaluator_export_denied").exists())
