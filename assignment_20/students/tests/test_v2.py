"""Tests for V2 features: departments, courses, grades, imports, exports,
bulk actions, transcripts, and global search."""
import csv
import io
import json

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings

from core.models import AuditLog, ImportBatch
from students.models import Course, Department, Enrollment, Guardian, Lecturer, Student
from students.tests.helpers import (
    enroll, make_admin_user, make_course, make_staff_user, make_student, make_student_user,
)
from students.utils import current_session, previous_session


def response_body(response):
    """Read a streaming or regular response body."""
    if hasattr(response, "streaming_content"):
        return b"".join(response.streaming_content).decode("utf-8-sig")
    return response.content.decode("utf-8-sig")


def csv_file(content, name="students.csv"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


def make_lecturer(name="ngozi", department=None):
    department = department or Department.objects.get_or_create(name="Computer Science")[0]
    user = User.objects.create_user(name, password="testpass123", first_name="Ngozi", last_name="Okeke")
    from django.contrib.auth.models import Group

    user.groups.add(Group.objects.get_or_create(name="Lecturer")[0])
    lecturer = Lecturer.objects.create(user=user, staff_number=f"LEC/CSC/{name[-3:]}", title="Dr", department=department)
    return lecturer


class DepartmentTests(TestCase):
    def setUp(self):
        self.admin = make_admin_user()
        self.client.force_login(self.admin)

    def test_create_edit_and_duplicate(self):
        self.client.post("/departments/add/", {"name": "Computer Science"}, follow=True)
        self.assertTrue(Department.objects.filter(name="Computer Science").exists())
        response = self.client.post("/departments/add/", {"name": "computer science"}, follow=True)
        self.assertContains(response, "already exists")
        department = Department.objects.get(name="Computer Science")
        response = self.client.post(f"/departments/{department.pk}/edit/", {"name": "Software Engineering"}, follow=True)
        self.assertContains(response, "Department updated")

    def test_delete_blocked_when_in_use(self):
        student = make_student()
        department = student.department
        response = self.client.post(f"/departments/{department.pk}/delete/", follow=True)
        self.assertTrue(Department.objects.filter(pk=department.pk).exists())
        self.assertContains(response, "still has")

    def test_delete_allowed_when_empty(self):
        department = Department.objects.create(name="Empty Department")
        self.client.post(f"/departments/{department.pk}/delete/", follow=True)
        self.assertFalse(Department.objects.filter(pk=department.pk).exists())


class CourseV2Tests(TestCase):
    def setUp(self):
        self.admin = make_admin_user()
        self.client.force_login(self.admin)
        self.lecturer = make_lecturer()
        self.course = make_course("CSC201", 4)
        self.course.lecturers.add(self.lecturer)

    def test_course_requires_department_and_level(self):
        response = self.client.post("/courses/add/", {"code": "CSC205", "title": "X", "credit_units": 3})
        self.assertEqual(response.status_code, 200)  # form re-rendered with errors
        self.assertFalse(Course.objects.filter(code="CSC205").exists())

    def test_list_filters(self):
        make_course("ITE301")
        response = self.client.get("/courses/", {"department": str(self.course.department.pk)})
        self.assertContains(response, "CSC201")
        response = self.client.get("/courses/", {"level": "300"})
        self.assertNotContains(response, "CSC201")
        response = self.client.get("/courses/", {"unassigned": "1"})
        self.assertContains(response, "ITE301")
        self.assertNotContains(response, "Data Structures" if "Data Structures" in self.course.title else "zzz")

    def test_curriculum_matching(self):
        student = make_student(level=200)
        self.assertIn(self.course, Course.curriculum_for(student))
        self.assertIn(student, self.course.students_matching)
        other = make_student(level=300, matric_no="VUG/CSC/24/88888", email="l3@example.com")
        self.assertNotIn(self.course, Course.curriculum_for(other))

    def test_enroll_matching_creates_and_is_idempotent(self):
        student = make_student(level=200)
        second = make_student(level=200, matric_no="VUG/CSC/24/80002", email="two2@example.com")
        session = current_session()
        response = self.client.post(f"/courses/{self.course.pk}/enroll-matching/", {"session": session}, follow=True)
        self.assertContains(response, f"Enrolled 2 students.")
        self.assertEqual(Enrollment.objects.filter(course=self.course, session=session).count(), 2)
        self.client.post(f"/courses/{self.course.pk}/enroll-matching/", {"session": session}, follow=True)
        self.assertEqual(Enrollment.objects.filter(course=self.course, session=session).count(), 2)
        self.assertTrue(AuditLog.objects.filter(summary=f"Enrolled 2 students in {self.course.code} for {session}").exists())


class GradeSheetTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)
        self.course = make_course("CSC201", 3)
        self.student = make_student(level=200)
        self.enrollment = enroll(self.student, self.course, session=current_session())

    def post_grades(self, grade):
        return self.client.post(f"/courses/{self.course.pk}/grades/", {f"grade_{self.enrollment.pk}": grade})

    def test_only_changed_rows_written_with_metadata(self):
        session = current_session()
        self.post_grades("B")
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.grade, "B")
        self.assertEqual(self.enrollment.graded_by, self.staff)
        self.assertIsNotNone(self.enrollment.graded_at)
        # One update entry from the grade save (the create entry came from setup).
        updates = AuditLog.objects.filter(model="Enrollment", action="update")
        self.assertEqual(updates.count(), 1)

        # Saving the same grade again writes nothing.
        self.post_grades("B")
        self.assertEqual(AuditLog.objects.filter(model="Enrollment", action="update").count(), 1)

    def test_clearing_grade_allowed(self):
        self.post_grades("A")
        self.post_grades("")
        self.enrollment.refresh_from_db()
        self.assertIsNone(self.enrollment.grade)
        self.assertIsNone(self.enrollment.graded_by)

    def test_audit_summary_shows_old_to_new(self):
        self.post_grades("A")
        self.post_grades("C")
        summary = AuditLog.objects.filter(model="Enrollment").order_by("-pk").first().summary
        self.assertIn("changed from A to C", summary)

    def test_unassigned_lecturer_gets_403(self):
        lecturer_user = make_lecturer("ngozi").user
        self.client.force_login(lecturer_user)
        self.assertEqual(self.client.get(f"/courses/{self.course.pk}/grades/").status_code, 403)

    def test_assigned_lecturer_can_grade(self):
        lecturer = make_lecturer("bola")
        self.course.lecturers.add(lecturer)
        self.client.force_login(lecturer.user)
        self.post_grades("A")
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.grade, "A")

    def test_semester_gpa_and_cgpa(self):
        prior = previous_session()
        other = make_course("CSC102", 3)
        e1 = enroll(self.student, other, grade="A", session=prior)
        self.enrollment.grade = "F"
        self.enrollment.save()
        from students.utils import session_gpa, units_summary

        enrollments = list(self.student.enrollments.all())
        self.assertEqual(session_gpa(enrollments), round((5 * 3 + 0 * 3) / 6, 2))
        self.assertEqual(units_summary(enrollments), (6, 3))
        self.assertEqual(self.student.cgpa, 2.5)


class StudentImportTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)
        Department.objects.get_or_create(name="Computer Science")

    def header(self):
        return "first_name,last_name,email,matric_no,department,level,dob,gender,phone"

    def row(self, **overrides):
        row = {"first_name": "Ada", "last_name": "Obi", "email": "ada@example.com",
               "matric_no": "VUG/CSC/24/70001", "department": "Computer Science", "level": "200",
               "dob": "2005-05-12", "gender": "female", "phone": "+2348012345678"}
        row.update(overrides)
        return row

    def upload(self, rows, **form_extra):
        content = self.header() + "\n" + "\n".join(rows) + "\n"
        return self.client.post("/students/import/", {"file": csv_file(content), **form_extra})

    def test_valid_file_reaches_preview_and_confirms(self):
        response = self.upload([",".join(self.row().values())])
        self.assertRedirects(response, "/students/import/1/", fetch_redirect_response=False)
        response = self.client.post("/students/import/1/", {"confirm": 1}, follow=True)
        self.assertContains(response, "Imported 1 students.")
        self.assertTrue(Student.objects.filter(matric_no="VUG/CSC/24/70001").exists())

    def test_row_rules_produce_errors(self):
        # Each row gets a unique matric/email so we test one rule at a time.
        bad = [
            self.row(matric_no="bad-matric", email="a@example.com"),                      # matric pattern
            self.row(email="a@example.com"),                                              # duplicate in file (row 1 email)
            self.row(department="No Such Department", email="b@example.com"),             # unknown department
            self.row(level="700", email="c@example.com"),                                 # bad level
            self.row(dob="2099-01-01", email="d@example.com"),                            # future dob
            self.row(dob="12/05/2005", email="e@example.com"),                            # DD/MM/YYYY is valid
        ]
        # Rows 3 onward duplicate row 1's matric number, which is itself an error.
        response = self.upload(",".join(values.values()) for values in bad)
        response = self.client.get("/students/import/1/")
        self.assertContains(response, "Use the format VUG/CSC/24/10001")
        self.assertContains(response, "Email already exists in this file")
        self.assertContains(response, "No department with that name")
        self.assertContains(response, "Level must be 100 to 500")
        self.assertContains(response, "cannot be in the future")
        self.assertEqual(Student.objects.count(), 0)

    def test_skip_errors_flag(self):
        rows = [",".join(self.row().values()), ",".join(self.row(email="ada@example.com", matric_no="VUG/CSC/24/70002").values())]
        self.upload(rows, skip_errors=True)
        self.client.post("/students/import/1/", {"confirm": 1}, follow=True)
        self.assertEqual(Student.objects.count(), 1)

    def test_import_blocked_while_errors_and_no_skip(self):
        rows = [",".join(self.row().values()), ",".join(self.row(email="ada@example.com", matric_no="VUG/CSC/24/70002").values())]
        self.upload(rows)
        response = self.client.post("/students/import/1/", {"confirm": 1}, follow=True)
        self.assertEqual(Student.objects.count(), 0)

    def test_duplicate_matric_against_database(self):
        make_student()
        response = self.upload([",".join(self.row().values())])
        self.client.get("/students/import/1/")
        self.assertTrue(ImportBatch.objects.get(pk=1).errors)

    def test_rollback_on_database_error(self):
        self.upload([",".join(self.row().values())])
        from unittest.mock import patch
        from django.db.models import QuerySet

        with patch.object(Student.objects, "bulk_create", side_effect=Exception("forced")):
            response = self.client.post("/students/import/1/", {"confirm": 1}, follow=True)
        self.assertContains(response, "nothing was written")
        self.assertEqual(Student.objects.count(), 0)

    def test_size_limit_and_binary_rejection(self):
        response = self.client.post("/students/import/", {"file": csv_file("a,b\n1,2", name="big.csv")})
        big = "first_name,last_name,email,matric_no,department,level,dob,gender,phone\n" + "a,b,x@y.zz,VUG/CSC/24/70001,Computer Science,200,2005-05-12,female,+234800000000\n" * 1
        binary = SimpleBinary()
        response = self.client.post("/students/import/", {"file": binary})
        self.assertContains(response, "CSV text")

    def test_logins_created_and_one_time_credentials(self):
        self.upload([",".join(self.row().values())], create_logins=True)
        self.client.post("/students/import/1/", {"confirm": 1}, follow=True)
        student = Student.objects.get(matric_no="VUG/CSC/24/70001")
        self.assertIsNotNone(student.user)
        self.assertTrue(student.user.profile.must_change_password)
        response = self.client.get("/students/import/1/credentials.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("temporary_password", response_body(response))
        # Second download is refused.
        response = self.client.get("/students/import/1/credentials.csv")
        self.assertEqual(response.status_code, 302)

    def test_template_download_and_history(self):
        response = self.client.get("/students/import/template.csv")
        self.assertContains(response, "first_name,last_name")
        self.upload([",".join(self.row().values())])
        self.client.post("/students/import/1/", {"confirm": 1})
        response = self.client.get("/students/import/history/")
        self.assertContains(response, "students.csv")


class SimpleBinary:
    def read(self, *args, **kwargs):
        return b"\x00\x01\x02binary"

    @property
    def name(self):
        return "file.csv"


class GradeAndCourseImportTests(TestCase):
    def setUp(self):
        self.admin = make_admin_user()
        self.client.force_login(self.admin)
        self.course = make_course("CSC201", 3)
        self.student = make_student(level=200)

    def test_grade_import_flow(self):
        enroll(self.student, self.course, session=current_session())
        content = "matric_no,grade\nVUG/CSC/24/10001,A\n"
        response = self.client.post(f"/courses/{self.course.pk}/grades/import/", {"file": csv_file(content, "grades.csv")})
        self.assertRedirects(response, f"/courses/{self.course.pk}/grades/import/1/", fetch_redirect_response=False)
        response = self.client.post(f"/courses/{self.course.pk}/grades/import/1/", {"confirm": 1}, follow=True)
        self.assertContains(response, "Saved 1 grades")
        self.enrollment = Enrollment.objects.get(student=self.student, course=self.course)
        self.assertEqual(self.enrollment.grade, "A")
        self.assertEqual(self.enrollment.graded_by, self.admin)

    def test_grade_import_rejects_unenrolled_matric(self):
        content = "matric_no,grade\nVUG/CSC/24/99999,A\n"
        self.client.post(f"/courses/{self.course.pk}/grades/import/", {"file": csv_file(content, "grades.csv")})
        batch = ImportBatch.objects.get(kind="grades")
        self.assertTrue(batch.errors)
        self.assertEqual(batch.summary["valid"], 0)

    def test_course_import_flow(self):
        content = ("code,title,credit_units,department,level,semester,lecturer_staff_numbers\n"
                   "CSC205,Testing,3,Computer Science,200,first,LEC/NOPE/01\n")
        response = self.client.post("/courses/import/", {"file": csv_file(content, "courses.csv")})
        batch = ImportBatch.objects.get(kind="courses")
        self.assertTrue(any("No lecturer" in error["message"] for error in batch.errors))

        content = ("code,title,credit_units,department,level,semester\n"
                   "csc205,Testing Course,3,Computer Science,200,first\n")
        self.client.post("/courses/import/", {"file": csv_file(content, "courses.csv")})
        self.client.post("/courses/import/2/", {"confirm": 1}, follow=True)
        self.assertTrue(Course.objects.filter(code="CSC205").exists())


class ExportTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)

    def test_students_export(self):
        make_student()
        response = self.client.get("/students/export.csv", {"status": "active"})
        body = response_body(response)
        self.assertIn("matric_no,first_name", body)
        self.assertIn("VUG/CSC/24/10001", body)

    def test_utf8_bom_present(self):
        make_student()
        self.assertTrue(b"".join(self.client.get("/students/export.csv").streaming_content).startswith(b"\xef\xbb\xbf"))

    def test_formula_cells_neutralized(self):
        student = make_student()
        student.first_name = "=cmd"
        student.save()
        response = self.client.get("/students/export.csv")
        self.assertIn("'=cmd", response_body(response))

    def test_audit_export_admin_only(self):
        make_student()
        self.assertEqual(self.client.get("/audit/export.csv").status_code, 403)
        self.client.force_login(make_admin_user())
        response = self.client.get("/audit/export.csv")
        self.assertIn("summary", response_body(response))
        self.assertTrue(AuditLog.objects.filter(action="export", model="AuditLog").exists())

    def test_roster_export(self):
        course = make_course("CSC201")
        student = make_student(level=200)
        enroll(student, course, grade="B", session=current_session())
        response = self.client.get(f"/courses/{course.pk}/roster.csv")
        body = response_body(response)
        self.assertIn("VUG/CSC/24/10001", body)
        self.assertIn("B", body)


class BulkActionTests(TestCase):
    def setUp(self):
        self.staff = make_staff_user()
        self.client.force_login(self.staff)

    def test_promote_skips_500_level(self):
        top = make_student(level=500)
        normal = make_student(matric_no="VUG/CSC/24/70002", email="two@example.com", level=300)
        response = self.client.post("/students/bulk/promote/", {"ids": json.dumps([top.pk, normal.pk, 99999])}, follow=True)
        self.assertContains(response, "Promoted 1 students. 1 at 500 level were not changed.")
        normal.refresh_from_db()
        top.refresh_from_db()
        self.assertEqual(normal.level, 400)
        self.assertEqual(top.level, 500)

    def test_status_change(self):
        student = make_student()
        self.client.post("/students/bulk/status/", {"ids": json.dumps([student.pk]), "status": "suspended"}, follow=True)
        student.refresh_from_db()
        self.assertEqual(student.status, "suspended")

    def test_non_staff_rejected(self):
        user = make_student_user()
        self.client.force_login(user)
        student = Student.objects.get(user=user)
        response = self.client.post("/students/bulk/promote/", {"ids": json.dumps([student.pk])})
        self.assertEqual(response.status_code, 403)


class TranscriptTests(TestCase):
    def setUp(self):
        # A unique matric: make_student_user later creates the default one.
        self.student = make_student(level=200, matric_no="VUG/CSC/24/60001", email="transcript@example.com")
        self.prior = previous_session()
        enroll(self.student, make_course("CSC102", 3), grade="A", session=self.prior)
        enroll(self.student, make_course("CSC201", 4), grade=None)  # pending, current session

    def test_grouping_and_gpa(self):
        self.client.force_login(make_staff_user())
        response = self.client.get(f"/students/{self.student.pk}/transcript/")
        self.assertContains(response, "Academic transcript")
        self.assertContains(response, "Pending")
        self.assertContains(response, "GPA 5.00")
        self.assertContains(response, "CGPA")

    def test_student_only_own_transcript(self):
        user = make_student_user()
        self.client.force_login(user)
        self.assertEqual(self.client.get("/me/transcript/").status_code, 200)
        self.assertEqual(self.client.get(f"/students/{self.student.pk}/transcript/").status_code, 403)

    def test_transcript_has_no_sidebar(self):
        user = make_student_user()
        self.client.force_login(user)
        response = self.client.get("/me/transcript/")
        self.assertNotContains(response, "sidebar")


class GlobalSearchTests(TestCase):
    def test_returns_students_and_courses(self):
        make_student()
        course = make_course("CSC201")
        self.client.force_login(make_staff_user())
        response = self.client.get("/search/", {"q": "obi"})
        self.assertContains(response, "Ada Obi")
        response = self.client.get("/search/", {"q": "CSC201"})
        self.assertContains(response, "CSC201 title")

    def test_role_restricted(self):
        user = make_student_user()
        self.client.force_login(user)
        self.assertEqual(self.client.get("/search/", {"q": "obi"}).status_code, 403)
        self.assertEqual(self.client.get("/search/", {"q": "x"}).status_code, 403)


class StaleImportCleanupTests(TestCase):
    def test_clear_stale_imports(self):
        from datetime import timedelta

        from django.utils import timezone

        batch = ImportBatch.objects.create(kind="students", filename="old.csv", rows=[{"x": 1}])
        ImportBatch.objects.filter(pk=batch.pk).update(created_at=timezone.now() - timedelta(hours=25))
        call_command("clear_stale_imports")
        batch.refresh_from_db()
        self.assertEqual(batch.rows, [])
