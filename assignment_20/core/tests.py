from django.core.management import call_command
from django.test import TestCase

from core.models import AuditLog
from students.models import Department
from students.tests.helpers import (
    make_admin_user, make_course, make_staff_user, make_student,
)


class AuditLogTests(TestCase):
    def setUp(self):
        self.admin = make_admin_user()
        self.client.force_login(self.admin)

    def valid_data(self, **overrides):
        department, _ = Department.objects.get_or_create(name="Computer Science")
        data = {
            "first_name": "Ada", "last_name": "Obi", "email": "ada@example.com",
            "phone": "+2348012345678", "dob": "2005-05-12", "gender": "female",
            "matric_no": "VUG/CSC/24/10001", "department": department.pk,
            "level": "200", "status": "active", "enrolled_on": "2025-01-10",
            "guardians-TOTAL_FORMS": "0", "guardians-INITIAL_FORMS": "0",
        }
        data.update(overrides)
        return data

    def test_create_is_logged(self):
        self.client.post("/students/add/", self.valid_data())
        log = AuditLog.objects.get(action="create", model="Student")
        self.assertEqual(log.actor, self.admin)
        self.assertIn("10001", log.summary)

    def test_update_is_logged(self):
        student = make_student()
        self.client.post(f"/students/{student.pk}/edit/", self.valid_data(first_name="Adaeze"))
        log = AuditLog.objects.get(action="update", model="Student")
        self.assertEqual(log.actor, self.admin)

    def test_delete_logs_snapshot(self):
        student = make_student()
        self.client.post(f"/students/{student.pk}/delete/")
        log = AuditLog.objects.get(action="delete", model="Student")
        self.assertEqual(log.snapshot["matric_no"], "VUG/CSC/24/10001")
        self.assertEqual(log.snapshot["name"], "Ada Obi")

    def test_course_and_enrollment_logging(self):
        course = make_course()
        self.client.post("/courses/add/", {"code": "CSC102", "title": "New", "credit_units": 3, "department": course.department.pk})
        self.assertTrue(AuditLog.objects.filter(action="create", model="Course").exists())
        student = make_student()
        self.client.post(f"/students/{student.pk}/enroll/", {"course": course.pk, "session": "2025/2026", "semester": "first", "grade": ""})
        self.assertTrue(AuditLog.objects.filter(action="create", model="Enrollment").exists())

    def test_audit_log_page_and_filters(self):
        make_student()
        response = self.client.get("/audit/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/audit/", {"action": "create", "model": "Student"})
        self.assertEqual(response.status_code, 200)


class DashboardTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)

    def test_counts_and_pages(self):
        make_student()
        make_student(matric_no="VUG/CSC/24/10002", email="two@example.com", status="graduated")
        make_student(matric_no="VUG/CSC/24/10003", email="three@example.com", status="suspended")
        response = self.client.get("/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["counts"]["total"], 3)
        self.assertEqual(response.context["counts"]["active"], 1)
        self.assertEqual(response.context["counts"]["graduated"], 1)
        self.assertEqual(response.context["counts"]["inactive"], 1)

    def test_charts_json_shape(self):
        make_student()
        response = self.client.get("/dashboard/charts.json")
        data = response.json()
        self.assertEqual(set(data), {"departments", "trend", "status"})
        self.assertEqual(data["status"]["labels"], ["Active", "Graduated", "Suspended", "Withdrawn"])
        self.assertEqual(sum(data["status"]["values"]), 1)
        self.assertEqual(len(data["trend"]["labels"]), 12)
        self.assertEqual(len(data["trend"]["values"]), 12)
        self.assertEqual(sum(data["trend"]["values"]), 1)


class PublicPagesTests(TestCase):
    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Management System")

    def test_error_pages(self):
        response = self.client.get("/no/such/page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "We could not find that page", status_code=404)
