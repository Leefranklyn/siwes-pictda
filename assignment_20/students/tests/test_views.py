from django.test import TestCase
from django.urls import reverse

from students.models import Guardian, Student
from students.tests.helpers import (
    Department, enroll, make_admin_user, make_course, make_staff_user, make_student,
)


class StudentListViewTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)
        self.alpha = make_student(matric_no="VUG/CSC/24/10001", first_name="Ada", last_name="Obi", email="ada@example.com")
        self.beta = make_student(matric_no="VUG/CSC/24/10002", first_name="John", last_name="Adams", email="john@example.com", status="graduated", level=300)

    def test_full_page_without_htmx(self):
        response = self.client.get("/students/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/student_list.html")
        self.assertContains(response, "Ada Obi")

    def test_htmx_request_returns_partial(self):
        response = self.client.get("/students/", headers={"HX-Request": "true"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/_table.html")

    def test_search_matches_name_and_matric(self):
        response = self.client.get("/students/", {"q": "obi"}, headers={"HX-Request": "true"})
        self.assertContains(response, "Ada Obi")
        self.assertNotContains(response, "John Adams")
        response = self.client.get("/students/", {"q": "10002"})
        self.assertContains(response, "John Adams")

    def test_filters(self):
        response = self.client.get("/students/", {"status": "graduated"})
        self.assertContains(response, "John Adams")
        self.assertNotContains(response, "Ada Obi")
        response = self.client.get("/students/", {"level": "200"})
        self.assertContains(response, "Ada Obi")
        response = self.client.get("/students/", {"department": "99999"})
        self.assertContains(response, "No students found")

    def test_sorting_and_invalid_fallback(self):
        response = self.client.get("/students/", {"sort": "name"})
        names = [student.last_name for student in response.context["students"]]
        self.assertEqual(names, sorted(names))
        response = self.client.get("/students/", {"sort": "DROP TABLE"})
        self.assertEqual(response.context["sort"], "name")
        response = self.client.get("/students/", {"sort": "-created_at"})
        self.assertEqual(response.context["sort"], "-created_at")

    def test_pagination(self):
        for index in range(25):
            make_student(matric_no=f"VUG/CSC/24/{20000 + index}", email=f"s{index}@example.com")
        response = self.client.get("/students/")
        self.assertEqual(len(response.context["students"]), 10)
        response = self.client.get("/students/", {"page": 3})
        self.assertEqual(response.status_code, 200)
        response = self.client.get("/students/", {"page": "not-a-page"})
        self.assertEqual(response.status_code, 404)


class StudentCrudTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)
        self.department, _ = Department.objects.get_or_create(name="Computer Science")

    def valid_data(self, **overrides):
        data = {
            "first_name": "Ada", "last_name": "Obi", "email": "ada@example.com",
            "phone": "+2348012345678", "dob": "2005-05-12", "gender": "female",
            "matric_no": "VUG/CSC/24/10001", "department": self.department.pk,
            "level": "200", "status": "active", "enrolled_on": "2025-01-10",
            "guardians-TOTAL_FORMS": "0", "guardians-INITIAL_FORMS": "0",
        }
        data.update(overrides)
        return data

    def test_create_redirects_and_flashes(self):
        response = self.client.post("/students/add/", self.valid_data(), follow=True)
        student = Student.objects.get(matric_no="VUG/CSC/24/10001")
        self.assertRedirects(response, student.get_absolute_url())
        self.assertContains(response, "Student added.")

    def test_create_with_guardian(self):
        data = self.valid_data(
            **{"guardians-TOTAL_FORMS": "1", "guardians-INITIAL_FORMS": "0",
               "guardians-0-full_name": "Bola Obi", "guardians-0-relationship": "Mother",
               "guardians-0-phone": "+2348023456789", "guardians-0-email": ""}
        )
        self.client.post("/students/add/", data)
        self.assertEqual(Guardian.objects.count(), 1)

    def test_create_rejects_duplicates_and_bad_phone_and_future_dob(self):
        response = self.client.post("/students/add/", self.valid_data())
        self.assertEqual(response.status_code, 302)
        response = self.client.post("/students/add/", self.valid_data(email="ADA@example.com"))
        self.assertContains(response, "already exists", status_code=200)
        response = self.client.post("/students/add/", self.valid_data(phone="080-abc"))
        self.assertContains(response, "Enter a valid phone number", status_code=200)
        response = self.client.post("/students/add/", self.valid_data(dob="2099-01-01"))
        self.assertContains(response, "cannot be in the future", status_code=200)

    def test_update(self):
        student = make_student()
        response = self.client.post(f"/students/{student.pk}/edit/", self.valid_data(first_name="Adaeze"))
        self.assertRedirects(response, student.get_absolute_url())
        student.refresh_from_db()
        self.assertEqual(student.first_name, "Adaeze")

    def test_delete(self):
        student = make_student()
        response = self.client.get(f"/students/{student.pk}/delete/")
        self.assertContains(response, "Delete this student?")
        response = self.client.post(f"/students/{student.pk}/delete/")
        self.assertRedirects(response, "/students/")
        self.assertFalse(Student.objects.filter(pk=student.pk).exists())


class EnrollmentTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)
        self.student = make_student()
        self.course = make_course()

    def test_add_enrollment(self):
        response = self.client.post(f"/students/{self.student.pk}/enroll/", {
            "course": self.course.pk, "session": "2025/2026", "semester": "first", "grade": "",
        })
        self.assertRedirects(response, self.student.get_absolute_url())
        self.assertEqual(self.student.enrollments.count(), 1)

    def test_duplicate_enrollment_rejected(self):
        enroll(self.student, self.course)
        response = self.client.post(f"/students/{self.student.pk}/enroll/", {
            "course": self.course.pk, "session": "2025/2026", "semester": "first", "grade": "",
        })
        self.assertContains(response, "already enrolled", status_code=200)

    def test_remove_enrollment(self):
        enrollment = enroll(self.student, self.course)
        response = self.client.post(f"/students/{self.student.pk}/enroll/{enrollment.pk}/remove/")
        self.assertRedirects(response, self.student.get_absolute_url())
        self.assertEqual(self.student.enrollments.count(), 0)


class CourseViewTests(TestCase):
    def setUp(self):
        self.admin = make_admin_user()
        self.client.force_login(self.admin)
        self.course = make_course()

    def test_list_and_create(self):
        response = self.client.get("/courses/")
        self.assertContains(response, "CSC101")
        # V2: courses also need a level and semester.
        response = self.client.post("/courses/add/", {"code": "csc102", "title": "New course", "credit_units": 3, "department": self.course.department.pk, "level": "200", "semester": "first"})
        self.assertRedirects(response, "/courses/")
        self.assertTrue(self.course.__class__.objects.filter(code="CSC102").exists())

    def test_edit(self):
        response = self.client.post(f"/courses/{self.course.pk}/edit/", {"code": "CSC101", "title": "Updated", "credit_units": 4, "department": self.course.department.pk, "level": "200", "semester": "first"})
        self.assertRedirects(response, "/courses/")
        self.course.refresh_from_db()
        self.assertEqual(self.course.credit_units, 4)
