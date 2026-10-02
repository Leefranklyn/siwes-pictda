from django.test import TestCase

from students.tests.test_models import make_student


class PermissionMatrixTests(TestCase):
    STAFF_URLS = ["/students/", "/students/add/", "/dashboard/", "/dashboard/charts.json"]
    ADMIN_URLS = ["/courses/", "/audit/"]

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
        from django.contrib.auth.models import User
        student = make_student()
        user = User.objects.create_user("student_user", password="testpass123")
        student.user = user
        student.save()
        self.client.force_login(user)
        for url in self.STAFF_URLS + self.ADMIN_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_student_sees_own_record(self):
        from django.contrib.auth.models import User
        student = make_student()
        user = User.objects.create_user("student_user", password="testpass123")
        student.user = user
        student.save()
        self.client.force_login(user)
        response = self.client.get("/me/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, student.full_name)

    def test_student_cannot_open_another_record(self):
        from django.contrib.auth.models import User
        make_student()
        other = make_student(matric_no="VUG/CSC/24/10002", email="other@example.com")
        user = User.objects.create_user("student_user", password="testpass123")
        make_student(user=user, matric_no="VUG/CSC/24/10003", email="mine@example.com")
        self.client.force_login(user)
        response = self.client.get(f"/students/{other.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_staff_allowed_and_admin_only_blocked(self):
        from django.contrib.auth.models import Group
        from students.tests.test_views import make_staff_user
        user = make_staff_user()
        self.client.force_login(user)
        for url in self.STAFF_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
        for url in self.ADMIN_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)
        Group.objects.get(name="Staff")

    def test_admin_redirected_from_me(self):
        from students.tests.test_views import make_admin_user
        self.client.force_login(make_admin_user())
        response = self.client.get("/me/")
        self.assertEqual(response.status_code, 302)

    def test_admin_allowed_everywhere(self):
        from students.tests.test_views import make_admin_user
        self.client.force_login(make_admin_user())
        urls = [url for url in self.all_urls() if url != "/me/"]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_staff_redirected_from_me(self):
        from students.tests.test_views import make_staff_user
        self.client.force_login(make_staff_user())
        response = self.client.get("/me/")
        self.assertEqual(response.status_code, 302)


class LoginViewTests(TestCase):
    def test_login_page_renders(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in")

    def test_student_login_goes_to_me(self):
        from django.contrib.auth.models import User
        student = make_student()
        user = User.objects.create_user("student_user", password="testpass123")
        student.user = user
        student.save()
        response = self.client.post("/accounts/login/", {"username": "student_user", "password": "testpass123"}, follow=True)
        self.assertRedirects(response, "/me/")

    def test_staff_login_goes_to_dashboard(self):
        from students.tests.test_views import make_staff_user
        self.client.force_login(make_staff_user())
        response = self.client.post("/accounts/login/", {"username": "staff_user", "password": "testpass123"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/dashboard/")

    def test_bad_credentials_show_message(self):
        response = self.client.post("/accounts/login/", {"username": "nobody", "password": "wrong"}, follow=True)
        self.assertContains(response, "do not match")

    def test_logout(self):
        from students.tests.test_views import make_staff_user
        self.client.force_login(make_staff_user())
        response = self.client.post("/accounts/logout/")
        self.assertEqual(response.status_code, 302)
