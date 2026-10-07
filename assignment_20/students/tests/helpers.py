"""Small setup helpers shared by the test modules."""
from django.contrib.auth.models import Group, User

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
    """A course with its level derived from the code, like CSC201 is 200 level."""
    department, _ = Department.objects.get_or_create(name="Computer Science")
    digits = "".join(char for char in code if char.isdigit())
    level = int(digits[-3]) * 100 if len(digits) >= 3 else 100
    return Course.objects.create(code=code, title=f"{code} title", credit_units=units,
                                 department=department, level=level)


def enroll(student, course, grade=None, session="2025/2026", semester="first"):
    return Enrollment.objects.create(student=student, course=course, session=session, semester=semester, grade=grade)


def make_user(username, group_name):
    user = User.objects.create_user(username, password="testpass123")
    user.groups.add(Group.objects.get_or_create(name=group_name)[0])
    return user


def make_staff_user():
    return make_user("staff_user", "Staff")


def make_admin_user():
    return make_user("admin_user", "Admin")


def make_student_user():
    """A user attached to a student record, i.e. the student role."""
    student = make_student()
    user = User.objects.create_user("student_user", password="testpass123")
    student.user = user
    student.save()
    return user
