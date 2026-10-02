from django.test import TestCase

from students.models import Course, Department, Enrollment, Student


def make_student(**overrides):
    department, _ = Department.objects.get_or_create(name="Computer Science")
    fields = {
        "matric_no": "VUG/CSC/24/10001", "first_name": "Ada", "last_name": "Obi",
        "email": "ada@example.com", "phone": "+2348012345678", "dob": "2005-05-12",
        "gender": "female", "department": department, "level": 200, "status": "active",
    }
    fields.update(overrides)
    return Student.objects.create(**fields)


def make_course(code="CSC101", units=3):
    department, _ = Department.objects.get_or_create(name="Computer Science")
    return Course.objects.create(code=code, title=f"{code} title", credit_units=units, department=department)


def enroll(student, course, grade=None, session="2025/2026", semester="first"):
    return Enrollment.objects.create(student=student, course=course, session=session, semester=semester, grade=grade)


class CgpaTests(TestCase):
    def test_no_grades_returns_none(self):
        student = make_student()
        enroll(student, make_course())
        self.assertIsNone(student.cgpa)

    def test_mixed_graded_and_ungraded(self):
        student = make_student()
        enroll(student, make_course("CSC101", 3), grade="A")
        enroll(student, make_course("CSC102", 4))
        self.assertEqual(student.cgpa, 5.0)

    def test_weighting_by_credit_units(self):
        student = make_student()
        enroll(student, make_course("CSC101", 3), grade="A")
        enroll(student, make_course("CSC102", 1), grade="F")
        self.assertEqual(student.cgpa, 3.75)

    def test_all_grade_values(self):
        student = make_student()
        points = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}
        for index, (grade, expected) in enumerate(points.items()):
            enroll(student, make_course(f"CSC{index + 10}", 1), grade=grade)
        self.assertEqual(student.cgpa, round(sum(points.values()) / len(points), 2))


class ModelTests(TestCase):
    def test_matric_number_saved_uppercase(self):
        student = make_student(matric_no="vug/csc/24/10001")
        self.assertEqual(student.matric_no, "VUG/CSC/24/10001")
        self.assertEqual(str(student), "Obi, Ada (VUG/CSC/24/10001)")

    def test_full_name_and_absolute_url(self):
        student = make_student()
        self.assertEqual(student.full_name, "Ada Obi")
        self.assertEqual(student.get_absolute_url(), f"/students/{student.pk}/")

    def test_duplicate_matric_case_insensitive(self):
        make_student()
        with self.assertRaises(Exception):
            make_student(email="other@example.com")

    def test_duplicate_email_case_insensitive(self):
        make_student()
        with self.assertRaises(Exception):
            make_student(matric_no="VUG/CSC/24/10002")
