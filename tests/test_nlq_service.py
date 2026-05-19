from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import CustomUser
from applications.models import IPApplication
from cases.models import Case


def create_user(email, role=CustomUser.Role.APPLICANT):
    return CustomUser.objects.create_user(
        email=email,
        password="StrongPass123!",
        first_name="Test",
        last_name="User",
        role=role,
        is_staff=role == CustomUser.Role.ADMIN,
    )


class NLQProcessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = create_user("admin-nlq@example.com", CustomUser.Role.ADMIN)
        self.applicant = create_user("applicant-nlq@example.com")
        self.client.force_authenticate(self.admin)

    def create_application(self, ip_type=IPApplication.IPType.PATENT, title="Test IP"):
        return IPApplication.objects.create(
            applicant=self.applicant,
            ip_type=ip_type,
            title=title,
            description="A test intellectual property application.",
            declaration_accepted=True,
        )

    def post_query(self, query):
        return self.client.post("/api/nlq/process/", {"query": query}, format="json")

    def test_show_all_applications_uses_application_intent(self):
        self.create_application(IPApplication.IPType.PATENT, "Patent filing")
        self.create_application(IPApplication.IPType.TRADEMARK, "Trademark filing")

        response = self.post_query("Show me all applications")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "filtered_applications")
        self.assertEqual(response.data["filters"], {})
        self.assertEqual(response.data["result_count"], 2)

    def test_show_approved_patent_applications_detects_status_and_ip_type(self):
        application = self.create_application(IPApplication.IPType.PATENT, "Approved patent")
        Case.objects.create(
            application=application,
            applicant=self.applicant,
            status=Case.Status.CERTIFIED,
        )
        self.create_application(IPApplication.IPType.TRADEMARK, "Unmatched trademark")

        response = self.post_query("Show approved patent applications")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "filtered_applications")
        self.assertEqual(response.data["filters"], {"ip_type": "patent", "status": "approved"})
        self.assertEqual(response.data["result_count"], 1)

    def test_existing_pending_patent_case_query_still_works(self):
        patent_application = self.create_application(IPApplication.IPType.PATENT, "Pending patent")
        trademark_application = self.create_application(IPApplication.IPType.TRADEMARK, "Pending trademark")
        Case.objects.create(
            application=patent_application,
            applicant=self.applicant,
            status=Case.Status.PENDING,
        )
        Case.objects.create(
            application=trademark_application,
            applicant=self.applicant,
            status=Case.Status.PENDING,
        )

        response = self.post_query("Show pending patent cases")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["intent"], "filtered_cases")
        self.assertEqual(response.data["filters"], {"ip_type": "patent", "status": "pending"})
        self.assertEqual(response.data["result_count"], 1)
