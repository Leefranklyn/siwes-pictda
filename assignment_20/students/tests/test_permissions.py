from django.test import TestCase

from students.models import Student
from students.tests.helpers import (
    make_admin_user, make_staff_user, make_student, make_student_user,
)


class PermissionMatrixTests(TestCase):
    # V2: staff may view the course list; creating and importing courses is admin only.
    STAFF_URLS = ["/students/", "/students/add/", "/dashboard/", "/dashboard/charts.json", "/courses/"]
    ADMIN_URLS = ["/courses/import/", "/audit/", "/departments/", "/accounts/manage/"]

    def all_urls(self):
        student = make_student()
        return self.STAFF_URLS + self.ADMIN_URLS + [f"/students/{student.pk}/", f"/students/{student.pk}/edit/", f"/students/{student.pk}/delete/", "/me/"]

    def test_anonymous_redirects_to_login(self):
        for url in self.all_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response["Location"])

    def test_student_blocked_from_staff_views(self):
        self.client.force_login(make_student_user())
        for url in self.STAFF_URLS + self.ADMIN_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_student_sees_own_record(self):
        user = make_student_user()
        student = Student.objects.get(user=user)
        self.client.force_login(user)
        response = self.client.get("/me/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, student.full_name)

    def test_student_cannot_open_another_record(self):
        user = make_student_user()
        other = make_student(matric_no="VUG/CSC/24/10002", email="other@example.com")
        self.client.force_login(user)
        response = self.client.get(f"/students/{other.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_staff_allowed_and_admin_only_blocked(self):
        self.client.force_login(make_staff_user())
        for url in self.STAFF_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
        for url in self.ADMIN_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_admin_redirected_from_me(self):
        self.client.force_login(make_admin_user())
        response = self.client.get("/me/")
        self.assertEqual(response.status_code, 302)

    def test_admin_allowed_everywhere(self):
        self.client.force_login(make_admin_user())
        urls = [url for url in self.all_urls() if url != "/me/"]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_staff_redirected_from_me(self):
        self.client.force_login(make_staff_user())
        response = self.client.get("/me/")
        self.assertEqual(response.status_code, 302)


class LoginViewTests(TestCase):
    def test_login_page_renders(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in")

    def test_student_login_goes_to_me(self):
        user = make_student_user()
        response = self.client.post("/accounts/login/", {"username": user.username, "password": "testpass123"}, follow=True)
        self.assertRedirects(response, "/me/")

    def test_staff_login_goes_to_dashboard(self):
        self.client.force_login(make_staff_user())
        response = self.client.post("/accounts/login/", {"username": "staff_user", "password": "testpass123"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/dashboard/")

    def test_bad_credentials_show_message(self):
        response = self.client.post("/accounts/login/", {"username": "nobody", "password": "wrong"}, follow=True)
        self.assertContains(response, "do not match")

    def test_logout(self):
        self.client.force_login(make_staff_user())
        response = self.client.post("/accounts/logout/")
        self.assertEqual(response.status_code, 302)
