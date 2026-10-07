"""Tests for the lecturer role, account management, and password flows."""
import json

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from io import StringIO

from core.models import AuditLog
from students.models import Department, Lecturer, Student
from students.tests.helpers import (
    enroll, make_admin_user, make_course, make_staff_user, make_student,
    make_student_user, make_user,
)
from students.tests.test_models import CgpaTests  # noqa: F401  (keeps V1 module importable)


def make_lecturer_user(department=None):
    user = User.objects.create_user("lecturer_user", password="testpass123", first_name="Ngozi", last_name="Okeke")
    Group.objects.get_or_create(name="Lecturer")[0].user_set.add(user)
    department = department or Department.objects.get_or_create(name="Computer Science")[0]
    Lecturer.objects.create(user=user, staff_number="LEC/CSC/042", title="Dr", department=department)
    return user


class LecturerRoleTests(TestCase):
    def test_lecturer_role_detected(self):
        from accounts.roles import LECTURER, user_role

        self.assertEqual(user_role(make_lecturer_user()), LECTURER)

    def test_lecturer_without_profile_is_not_lecturer(self):
        from accounts.roles import user_role

        user = User.objects.create_user("bare_lecturer", password="testpass123")
        user.groups.add(Group.objects.get_or_create(name="Lecturer")[0])
        self.assertIsNone(user_role(user))

    def test_can_grade_matrix(self):
        from accounts.roles import can_grade

        lecturer_user = make_lecturer_user()
        own_course = make_course("CSC201")
        own_course.lecturers.add(Lecturer.objects.get(user=lecturer_user))
        other_course = make_course("CSC301")
        self.assertTrue(can_grade(make_admin_user(), other_course))
        self.assertTrue(can_grade(make_staff_user(), other_course))
        self.assertTrue(can_grade(lecturer_user, own_course))
        self.assertFalse(can_grade(lecturer_user, other_course))
        make_student_user()
        self.assertFalse(can_grade(User.objects.get(username="student_user"), own_course))


class PermissionMatrixV2Tests(TestCase):
    LECTURER_URLS = ["/teaching/"]
    ADMIN_URLS = ["/courses/import/", "/departments/", "/departments/add/", "/accounts/manage/", "/accounts/manage/add/"]

    def all_urls(self):
        make_student()
        return self.ADMIN_URLS + ["/courses/", "/students/", "/accounts/password/change/"]

    def test_anonymous_redirects(self):
        for url in self.all_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_lecturer_allowed_and_blocked(self):
        lecturer_user = make_lecturer_user()
        course = make_course("CSC201")
        course.lecturers.add(Lecturer.objects.get(user=lecturer_user))
        self.client.force_login(lecturer_user)
        for url in self.LECTURER_URLS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.get(f"/courses/{course.pk}/").status_code, 200)
        self.assertEqual(self.client.get(f"/courses/{course.pk}/grades/").status_code, 200)
        for url in ["/dashboard/", "/students/", "/me/"] + self.ADMIN_URLS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_lecturer_cannot_open_other_course(self):
        lecturer_user = make_lecturer_user()
        other_course = make_course("CSC301")
        self.client.force_login(lecturer_user)
        self.assertEqual(self.client.get(f"/courses/{other_course.pk}/").status_code, 403)
        self.assertEqual(self.client.get(f"/courses/{other_course.pk}/grades/").status_code, 403)
        self.assertEqual(self.client.get(f"/courses/{other_course.pk}/roster.csv").status_code, 403)

    def test_admin_allowed_everywhere(self):
        self.client.force_login(make_admin_user())
        # /teaching/ and /me/ are role-specific pages tested on their own.
        for url in self.all_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class AccountManagementTests(TestCase):
    def setUp(self):
        self.admin = make_admin_user()
        self.client.force_login(self.admin)

    def account_data(self, role="student", **overrides):
        data = {"first_name": "Test", "last_name": "User", "email": "test.user@example.com",
                "username": "test_user", "role": role, "password": "TempPass20!"}
        if role == "student":
            data["student"] = make_student(email="linkme@example.com", matric_no="VUG/CSC/24/55555").pk
        if role == "lecturer":
            data.update({"staff_number": "LEC/CSC/077", "title": "Dr",
                         "department": Department.objects.get_or_create(name="Computer Science")[0].pk})
        data.update(overrides)
        return data

    def test_create_each_role(self):
        for index, role in enumerate(("admin", "staff", "lecturer", "student")):
            with self.subTest(role=role):
                data = self.account_data(role, username=f"user_{role}", email=f"{role}@example.com")
                if role == "student":
                    data["student"] = make_student(email=f"s{index}@example.com", matric_no=f"VUG/CSC/24/58{index:03d}").pk
                response = self.client.post("/accounts/manage/add/", data, follow=True)
                self.assertContains(response, "Account created")
                self.assertTrue(User.objects.filter(username=f"user_{role}").exists())

    def test_student_picker_shows_only_unlinked(self):
        linked = make_student(email="linked@example.com", matric_no="VUG/CSC/24/50001")
        make_student_user()  # creates a linked student and user
        free = make_student(email="free@example.com", matric_no="VUG/CSC/24/50002")
        linked.user = User.objects.create_user("linked_user", password="x")
        linked.save()
        response = self.client.get("/accounts/manage/link-students/")
        self.assertContains(response, str(free.pk))
        self.assertNotContains(response, f'value="{linked.pk}"')

    def test_temporary_password_never_in_audit_log(self):
        self.client.post("/accounts/manage/add/", self.account_data(role="staff"))
        for log in AuditLog.objects.all():
            self.assertNotIn("TempPass20!", log.summary)
            self.assertNotIn("TempPass20!", str(log.snapshot))

    def test_last_admin_cannot_be_demoted_or_deactivated(self):
        # The acting admin is a superuser, not an "Admin" group member, so the
        # target is the last active group admin and cannot be demoted.
        acting = User.objects.create_superuser("acting_admin", password="testpass123")
        self.client.force_login(acting)
        response = self.client.post(f"/accounts/manage/{self.admin.pk}/edit/", {
            "first_name": "Admin", "last_name": "User", "email": "admin@example.com",
            "username": self.admin.username, "role": "staff",
        })
        self.assertContains(response, "last active administrator", status_code=200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_cannot_deactivate_self(self):
        # A second active admin exists, so the last-admin guard does not apply.
        make_user("second_admin", "Admin")
        self.admin.username = "acting_admin"
        self.admin.email = "acting@example.com"
        self.admin.save()
        self.client.force_login(self.admin)
        response = self.client.post(f"/accounts/manage/{self.admin.pk}/edit/", {
            "first_name": "Admin", "last_name": "User", "email": "acting@example.com",
            "username": "acting_admin", "role": "admin",
        })
        self.assertContains(response, "deactivate yourself", status_code=200)

    def test_reset_password_sets_flag_and_logs(self):
        user = User.objects.create_user("reset_me", password="testpass123")
        response = self.client.post(f"/accounts/manage/{user.pk}/reset-password/", follow=True)
        self.assertContains(response, "Temporary password")
        user.refresh_from_db()
        self.assertTrue(user.profile.must_change_password)
        self.assertTrue(AuditLog.objects.filter(summary=f"Password reset for {user.username}").exists())

    def test_deactivate(self):
        user = User.objects.create_user("deactivate_me", password="testpass123")
        response = self.client.post(f"/accounts/manage/{user.pk}/toggle/", follow=True)
        self.assertContains(response, "Account updated")
        user.refresh_from_db()
        self.assertFalse(user.is_active)


class PasswordFlowTests(TestCase):
    def test_middleware_redirects_flagged_user(self):
        user = User.objects.create_user("flagged", password="testpass123")
        user.profile.must_change_password = True
        user.profile.save()
        self.client.force_login(user)
        response = self.client.get("/students/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/password/change/", response["Location"])

    def test_middleware_releases_after_change(self):
        user = User.objects.create_user("flagged2", password="testpass123")
        user.profile.must_change_password = True
        user.profile.save()
        self.client.force_login(user)
        response = self.client.post("/accounts/password/change/", {
            "old_password": "testpass123", "new_password1": "BrandNew20!pass", "new_password2": "BrandNew20!pass",
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.profile.must_change_password)
        # The middleware no longer forces the change page; the user simply has
        # no role, so /students/ is a normal 403 rather than a forced redirect.
        self.assertEqual(self.client.get("/students/").status_code, 403)

    def test_change_password_page_requires_login(self):
        self.assertEqual(self.client.get("/accounts/password/change/").status_code, 302)
        self.client.force_login(make_staff_user())
        self.assertEqual(self.client.get("/accounts/password/change/").status_code, 200)
