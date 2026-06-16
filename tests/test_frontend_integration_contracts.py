from pathlib import Path
import re

from django.test import SimpleTestCase


APP_JS = Path(__file__).resolve().parents[1] / "static" / "js" / "app.js"


def function_body(source, function_name):
    match = re.search(
        rf"(?:async\s+)?function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{",
        source,
    )
    if not match:
        raise AssertionError(f"Function {function_name} was not found.")
    depth = 1
    index = match.end()
    while index < len(source) and depth:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1
    return source[match.end():index - 1]


def assigned_function_body(source, function_name):
    match = re.search(
        rf"(?:window\.)?{re.escape(function_name)}\s*=\s*async\s+function\s*\([^)]*\)\s*\{{",
        source,
    )
    if not match:
        raise AssertionError(f"Assigned function {function_name} was not found.")
    depth = 1
    index = match.end()
    while index < len(source) and depth:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1
    return source[match.end():index - 1]


class FrontendIntegrationContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.source = APP_JS.read_text(encoding="utf-8")

    def test_application_prepares_case_and_uploads_before_submission(self):
        body = function_body(self.source, "createBackendApplication")

        prepare_index = body.index("prepare-case/")
        upload_index = body.index("uploadBackendApplicationDocuments")
        submit_index = body.index("/submit/")

        self.assertLess(prepare_index, upload_index)
        self.assertLess(upload_index, submit_index)

    def test_submit_form_stops_after_backend_failure(self):
        body = function_body(self.source, "submitForm")
        catch_match = re.search(
            r"catch\s*\(err\)\s*\{(?P<body>.*?)\}\s*(?:const\s+refNum|if\s*\(isPatentIntakeFlow)",
            body,
            re.DOTALL,
        )

        self.assertIsNotNone(catch_match)
        self.assertRegex(catch_match.group("body"), r"\breturn\s*;")

    def test_case_status_calls_use_update_status_post_endpoint(self):
        self.assertNotRegex(self.source, r"cases/\$\{[^}]+\}/status/")
        self.assertIn("/update-status/", self.source)

    def test_evaluator_queues_use_independent_loaders(self):
        available_body = function_body(self.source, "loadAvailableCases")
        my_cases_body = function_body(self.source, "loadMyCases")

        self.assertIn('apiRequest("cases/available/")', available_body)
        self.assertNotIn("cases/my-cases/", available_body)
        self.assertIn('apiRequest("cases/my-cases/")', my_cases_body)
        self.assertNotIn("cases/available/", my_cases_body)

    def test_evaluator_case_endpoint_errors_are_not_converted_to_empty_lists(self):
        self.assertNotIn('apiRequest("cases/available/").catch(() => [])', self.source)
        self.assertNotIn('apiRequest("cases/my-cases/").catch(() => [])', self.source)
        self.assertIn("resolveEvaluatorCasesError", self.source)

    def test_all_roles_continue_to_otp_after_credentials_are_accepted(self):
        body = function_body(self.source, "startLogin")

        self.assertNotIn('if (loginRole !== "applicant")', body)
        self.assertIn("showLoginOtpScreen", body)

    def test_notification_failures_are_not_converted_to_empty_success_data(self):
        self.assertNotIn('apiRequest("notifications/").catch(() => [])', self.source)
        self.assertIn("notificationsLoadError", self.source)

    def test_clear_notifications_does_not_mutate_local_state_after_failure(self):
        body = assigned_function_body(self.source, "clearCurrentRoleNotifications")
        catch_match = re.search(r"catch\s*\(err\)\s*\{(?P<body>.*?)\}", body, re.DOTALL)

        self.assertIsNotNone(catch_match)
        self.assertNotIn("mockNotifications", catch_match.group("body"))
        self.assertRegex(catch_match.group("body"), r"\breturn\s*;")

    def test_mark_notification_read_waits_for_backend_confirmation(self):
        body = function_body(self.source, "markNotificationRead")

        request_index = body.index("apiRequest(")
        mutation_index = body.index("notification.read = true")
        self.assertLess(request_index, mutation_index)
        self.assertNotIn(".catch(() => {})", body)

    def test_signup_verification_does_not_create_a_local_user(self):
        body = assigned_function_body(self.source, "verifySignupOtp")

        self.assertNotIn("createApplicantUserFromSignup", body)
        self.assertNotIn("systemUsers.push", body)
        self.assertIn('navigateTo("login")', body)

    def test_copyright_status_update_failure_is_not_swallowed(self):
        self.assertNotRegex(
            self.source,
            r"cases/\$\{submission\.backendCaseId\}/update-status/.*?catch\(\(\) => null\)",
        )

    def test_industrial_drawings_are_uploaded_as_drawing_documents(self):
        body = function_body(self.source, "uploadBackendApplicationDocuments")

        self.assertIn('"Drawing"', body)

    def test_evaluator_dashboard_failures_have_an_explicit_error_state(self):
        self.assertNotIn(
            'apiRequest("evaluator/dashboard-summary/").catch(() => null)',
            self.source,
        )
        self.assertNotIn(
            'apiRequest("evaluator/reports/cases-by-status/").catch(() => null)',
            self.source,
        )
        self.assertIn("evaluatorDashboardError", self.source)

    def test_case_detail_load_errors_are_not_silently_converted_to_empty_data(self):
        body = assigned_function_body(self.source, "viewSubmission")

        self.assertNotIn(".catch(() => [])", body)
        self.assertIn("showToast(", body)
