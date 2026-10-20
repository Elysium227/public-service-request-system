from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ServiceRequest


def make_request(citizen, **overrides):
    """Creates a service request with sensible defaults for the tests."""
    data = {
        "citizen": citizen,
        "category": "water",
        "priority": "medium",
        "location": "Nairobi",
        "description": "Burst pipe on the main road",
    }
    data.update(overrides)
    return ServiceRequest.objects.create(**data)


# A fast password hasher keeps the test run short. It is only used while testing.
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class BaseTestCase(TestCase):
    """Creates two citizens and one admin that every test class can use."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pass12345")
        self.bob = User.objects.create_user("bob", password="pass12345")
        self.admin = User.objects.create_user("admin", password="pass12345", is_staff=True)

    def login(self, user):
        self.client.login(username=user.username, password="pass12345")


class ModelTests(BaseTestCase):
    def test_reference_number_is_padded(self):
        service_request = make_request(self.alice)
        self.assertEqual(service_request.reference, f"REQ-{service_request.pk:04d}")

    def test_new_request_defaults(self):
        service_request = make_request(self.alice)
        self.assertEqual(service_request.status, "pending")
        self.assertEqual(service_request.priority, "medium")


class RegistrationTests(BaseTestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse("register"), {
            "username": "carol",
            "password1": "a-Strong-pass-77",
            "password2": "a-Strong-pass-77",
        })
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(username="carol").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(reverse("register"), {
            "username": "carol",
            "password1": "a-Strong-pass-77",
            "password2": "different-pass-88",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="carol").exists())


class SubmitRequestTests(BaseTestCase):
    def valid_data(self):
        return {
            "category": "streetlight",
            "priority": "high",
            "location": "Kisii",
            "description": "Light is out near the market",
        }

    def test_submit_requires_login(self):
        response = self.client.get(reverse("submit_request"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_submit_creates_request_for_logged_in_citizen(self):
        self.login(self.alice)
        response = self.client.post(reverse("submit_request"), self.valid_data())
        self.assertRedirects(response, reverse("my_requests"))
        created = ServiceRequest.objects.get()
        self.assertEqual(created.citizen, self.alice)
        self.assertEqual(created.status, "pending")
        self.assertEqual(created.priority, "high")

    def test_submit_shows_success_message_with_reference(self):
        self.login(self.alice)
        response = self.client.post(reverse("submit_request"), self.valid_data(), follow=True)
        self.assertContains(response, "REQ-")

    def test_submit_rejects_missing_description(self):
        self.login(self.alice)
        data = self.valid_data()
        data["description"] = ""
        response = self.client.post(reverse("submit_request"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ServiceRequest.objects.count(), 0)


class CitizenVisibilityTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.alice_request = make_request(self.alice, location="Alice Street")
        self.bob_request = make_request(self.bob, location="Bob Avenue")

    def test_my_requests_requires_login(self):
        response = self.client.get(reverse("my_requests"))
        self.assertEqual(response.status_code, 302)

    def test_my_requests_shows_only_own_requests(self):
        self.login(self.alice)
        response = self.client.get(reverse("my_requests"))
        self.assertContains(response, "Alice Street")
        self.assertNotContains(response, "Bob Avenue")

    def test_owner_can_open_detail_page(self):
        self.login(self.alice)
        response = self.client.get(reverse("request_detail", args=[self.alice_request.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alice_request.reference)

    def test_citizen_cannot_open_someone_elses_detail_page(self):
        self.login(self.alice)
        response = self.client.get(reverse("request_detail", args=[self.bob_request.pk]))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_open_any_detail_page(self):
        self.login(self.admin)
        response = self.client.get(reverse("request_detail", args=[self.bob_request.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detail_requires_login(self):
        response = self.client.get(reverse("request_detail", args=[self.alice_request.pk]))
        self.assertEqual(response.status_code, 302)

    def test_missing_request_returns_404(self):
        self.login(self.admin)
        response = self.client.get(reverse("request_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)


class AdminDashboardTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        make_request(self.alice, status="pending", category="water")
        make_request(self.alice, status="in_progress", category="road")
        make_request(self.bob, status="resolved", category="water")
        make_request(self.bob, status="resolved", category="garbage")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_is_forbidden_for_citizens(self):
        self.login(self.alice)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_counts_open_and_resolved(self):
        self.login(self.admin)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 4)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["in_progress_count"], 1)
        self.assertEqual(response.context["open_count"], 2)
        self.assertEqual(response.context["resolved_count"], 2)

    def test_dashboard_shows_all_citizens_requests(self):
        self.login(self.admin)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(len(response.context["all_requests"]), 4)

    def test_dashboard_filters_by_status(self):
        self.login(self.admin)
        response = self.client.get(reverse("admin_dashboard"), {"status": "resolved"})
        self.assertEqual(len(response.context["all_requests"]), 2)

    def test_dashboard_filters_by_category(self):
        self.login(self.admin)
        response = self.client.get(reverse("admin_dashboard"), {"category": "water"})
        self.assertEqual(len(response.context["all_requests"]), 2)

    def test_dashboard_with_no_requests_does_not_crash(self):
        ServiceRequest.objects.all().delete()
        self.login(self.admin)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pending_pct"], 0)


class UpdateStatusTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.service_request = make_request(self.alice)
        self.url = reverse("update_status", args=[self.service_request.pk])

    def test_staff_can_update_status(self):
        self.login(self.admin)
        response = self.client.post(self.url, {"status": "in_progress"})
        self.assertRedirects(response, reverse("admin_dashboard"))
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, "in_progress")

    def test_citizen_cannot_update_status(self):
        self.login(self.alice)
        response = self.client.post(self.url, {"status": "resolved"})
        self.assertEqual(response.status_code, 403)
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, "pending")

    def test_anonymous_user_cannot_update_status(self):
        response = self.client.post(self.url, {"status": "resolved"})
        self.assertEqual(response.status_code, 302)
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, "pending")

    def test_invalid_status_is_ignored(self):
        self.login(self.admin)
        self.client.post(self.url, {"status": "banana"})
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, "pending")

    def test_get_request_does_not_change_status(self):
        self.login(self.admin)
        self.client.get(self.url, {"status": "resolved"})
        self.service_request.refresh_from_db()
        self.assertEqual(self.service_request.status, "pending")

    def test_update_shows_success_message(self):
        self.login(self.admin)
        response = self.client.post(self.url, {"status": "resolved"}, follow=True)
        self.assertContains(response, "Status updated to Resolved")


class CsvExportTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        make_request(self.alice, status="pending", location="Alice Street")
        make_request(self.bob, status="resolved", location="Bob Avenue")

    def test_export_requires_staff(self):
        self.login(self.alice)
        response = self.client.get(reverse("export_csv"))
        self.assertEqual(response.status_code, 403)

    def test_export_requires_login(self):
        response = self.client.get(reverse("export_csv"))
        self.assertEqual(response.status_code, 302)

    def test_export_returns_csv_file_with_all_rows(self):
        self.login(self.admin)
        response = self.client.get(reverse("export_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("attachment", response["Content-Disposition"])
        content = response.content.decode("utf-8")
        self.assertIn("Reference", content)
        self.assertIn("Alice Street", content)
        self.assertIn("Bob Avenue", content)

    def test_export_respects_status_filter(self):
        self.login(self.admin)
        response = self.client.get(reverse("export_csv"), {"status": "resolved"})
        content = response.content.decode("utf-8")
        self.assertIn("Bob Avenue", content)
        self.assertNotIn("Alice Street", content)

    def test_export_neutralises_spreadsheet_formulas(self):
        make_request(self.alice, location="=HYPERLINK(\"http://example.com\")")
        self.login(self.admin)
        content = self.client.get(reverse("export_csv")).content.decode("utf-8")
        self.assertNotIn(",=HYPERLINK", content)
        self.assertIn("'=HYPERLINK", content)