import os
import random
import secrets
from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from students.models import Course, Department, Enrollment, Guardian, Lecturer, Student
from students.utils import current_session, previous_session

FIRST_NAMES = ["Adaeze", "Chinedu", "Fatima", "Ibrahim", "Kelechi", "Ngozi", "Olumide", "Aisha", "Emeka", "Zainab",
               "Tunde", "Chiamaka", "Yusuf", "Amara", "Obinna", "Halima", "Segun", "Uchenna", "Bola", "Ifeanyi",
               "Amina", "Damilola", "Nnamdi", "Funmilayo", "Ekene", "Rukayat", "Ogbemudia", "Chisom", "Musa", "Tomilayo"]
LAST_NAMES = ["Okafor", "Balogun", "Abubakar", "Eze", "Adeyemi", "Olawale", "Musa", "Nwosu", "Okonkwo", "Bello",
              "Ogunleye", "Umeh", "Aliyu", "Obi", "Adeola", "Danjuma", "Onyeka", "Sadiq", "Lawal", "Igwelo"]
RELATIONSHIPS = ["Mother", "Father", "Aunt", "Uncle", "Elder sister", "Elder brother"]
STATUSES = ["active"] * 7 + ["graduated", "suspended", "withdrawn"]
LECTURER_TITLES = ["Dr", "Prof", "Mr", "Dr", "Mrs"]
DEPARTMENTS = ["Computer Science", "Information Technology", "Software Engineering", "Cyber Security"]
DEPARTMENT_CODES = {"Computer Science": "CSC", "Information Technology": "ITE", "Software Engineering": "SEN", "Cyber Security": "CYS"}
COURSE_SEED = [
    ("CSC101", "Introduction to Computing", 3), ("CSC102", "Structured Programming", 4),
    ("CSC201", "Data Structures and Algorithms", 4), ("CSC202", "Computer Architecture", 3),
    ("CSC301", "Operating Systems", 3), ("CSC302", "Database Systems", 4),
    ("CSC401", "Software Engineering", 3), ("CSC402", "Computer Networks", 3),
    ("ITE201", "Digital Logic Design", 3), ("ITE301", "Web Development", 4),
    ("ITE302", "Human Computer Interaction", 2), ("SEN301", "Object Oriented Analysis", 3),
    ("SEN401", "Software Testing", 3), ("SEN402", "Software Project Management", 3),
    ("CYS301", "Network Security", 4), ("CYS401", "Ethical Hacking", 3),
]
GRADES = ["A", "B", "B", "C", "A", "C", "B", "A"]
DEMO_PASSWORDS = {"DEMO_ADMIN_PASSWORD": "LocalAdmin20!", "DEMO_STAFF_PASSWORD": "LocalStaff20!",
                  "DEMO_LECTURER_PASSWORD": "LocalLecturer20!", "DEMO_STUDENT_PASSWORD": "LocalStudent20!"}


class Command(BaseCommand):
    help = "Create idempotent demo data: departments, lecturers, courses, students, guardians, enrollments, groups, and demo users."

    def handle(self, *args, **options):
        random.seed(20)
        self.departments()
        self.lecturers()
        self.courses()
        self.students()
        self.users()
        self.demo_passwords()
        self.stdout.write("Demo data is ready.")

    def departments(self):
        for name in DEPARTMENTS:
            Department.objects.get_or_create(name=name)

    def lecturers(self):
        for index, name in enumerate(DEPARTMENTS):
            department = Department.objects.get(name=name)
            username = f"lecturer_{DEPARTMENT_CODES[name].lower()}{index + 1}"
            user = User.objects.get_or_create(
                username=username,
                defaults={"first_name": FIRST_NAMES[index], "last_name": LAST_NAMES[index],
                          "email": f"{username}@example.com"},
            )[0]
            if user.password == "" or not user.has_usable_password():
                user.set_password("LocalLecturer20!")
                user.save()
            Group.objects.get_or_create(name="Lecturer")[0].user_set.add(user)
            Lecturer.objects.get_or_create(
                staff_number=f"LEC/{DEPARTMENT_CODES[name]}/{index + 1:03d}",
                defaults={"user": user, "title": LECTURER_TITLES[index], "department": department,
                          "phone": f"+234{random.randint(600000000, 999999999)}"},
            )

    def courses(self):
        lecturers = Lecturer.objects.all()
        for index, (code, title, units) in enumerate(COURSE_SEED):
            prefix = code[:3]
            department_name = next((name for name in DEPARTMENTS if DEPARTMENT_CODES[name] == prefix), None)
            if department_name is None:
                continue
            department = Department.objects.get(name=department_name)
            digits = "".join(char for char in code if char.isdigit())
            level = int(digits[-3]) * 100
            semester = "second" if int(digits[-1]) % 2 == 0 else "first"
            course, created = Course.objects.get_or_create(
                code=code,
                defaults={"title": title, "credit_units": units, "department": department,
                          "level": level, "semester": semester},
            )
            if not course.lecturers.exists():
                course.lecturers.add(lecturers[index % len(lecturers)],
                                     lecturers[(index + 1) % len(lecturers)])

    def students(self):
        courses = list(Course.objects.all())
        today = date.today()
        session = current_session(today)
        prior = previous_session(today)
        for index in range(60):
            first = FIRST_NAMES[index % len(FIRST_NAMES)]
            last = LAST_NAMES[index % len(LAST_NAMES)]
            department = Department.objects.all()[index % len(DEPARTMENTS)]
            level = [100, 200, 300, 400, 500][index % 5]
            status = STATUSES[index % len(STATUSES)]
            matric = f"VUG/{DEPARTMENT_CODES[department.name]}/24/{10001 + index}"
            student, created = Student.objects.get_or_create(
                matric_no=matric,
                defaults={
                    "first_name": first, "last_name": last,
                    "email": f"{first.lower()}.{last.lower()}{index}@example.com",
                    "phone": f"+234{random.randint(600000000, 999999999)}",
                    "dob": date(today.year - 20, (index % 12) + 1, (index % 27) + 1),
                    "gender": ["female", "male", "other"][index % 3],
                    "address": f"{index + 1} Ahmadu Bello Way, Zaria",
                    "department": department, "level": level, "status": status,
                    "enrolled_on": today - timedelta(days=random.randint(0, 360)),
                },
            )
            if not created:
                continue
            Guardian.objects.get_or_create(
                student=student,
                defaults={
                    "full_name": f"{random.choice(LAST_NAMES)} {last}",
                    "relationship": RELATIONSHIPS[index % len(RELATIONSHIPS)],
                    "phone": f"+234{random.randint(600000000, 999999999)}", "email": "",
                },
            )
            curriculum = list(Course.objects.filter(department=department, level=level))
            if status == "active" and curriculum:
                self.enroll(student, curriculum, session)
                # A carry-over: one course from a lower level.
                carry = Course.objects.filter(department=department, level__lt=level).first()
                if carry and index % 4 == 0:
                    self.enroll(student, [carry], session)
            if level >= 200 and curriculum:
                # The previous session is graded, so transcripts show two sessions.
                self.enroll(student, curriculum, prior)
                for enrollment in student.enrollments.filter(session=prior):
                    enrollment.grade = GRADES[enrollment.course_id % len(GRADES)]
                    enrollment.save(update_fields=["grade"])
                    enrollment.save()

    def enroll(self, student, chosen, session=None):
        session = session or current_session()
        for course in chosen:
            Enrollment.objects.get_or_create(
                student=student, course=course, session=session,
                defaults={"semester": course.semester, "grade": None},
            )

    def users(self):
        for group_name in ("Admin", "Staff", "Lecturer"):
            Group.objects.get_or_create(name=group_name)
        accounts = [
            ("demo_admin", "Demo", "Admin", "Admin", "DEMO_ADMIN_PASSWORD"),
            ("demo_staff", "Demo", "Staff", "Staff", "DEMO_STAFF_PASSWORD"),
            ("demo_lecturer", "Demo", "Lecturer", "Lecturer", "DEMO_LECTURER_PASSWORD"),
            ("demo_student", "Adaeze", "Okafor", None, "DEMO_STUDENT_PASSWORD"),
        ]
        for username, first, last, group, password_var in accounts:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last, "email": f"{username}@example.com"},
            )
            if created:
                user.set_password(os.environ.get(password_var, DEMO_PASSWORDS[password_var]))
                user.save()
            if group:
                Group.objects.get(name=group).user_set.add(user)
            if username == "demo_lecturer":
                lecturer, created = Lecturer.objects.get_or_create(
                    user=user,
                    defaults={"staff_number": "LEC/CSC/099", "title": "Dr",
                              "department": Department.objects.get(name="Computer Science")},
                )
                if created:
                    lecturer.courses.set(Course.objects.filter(code__in=["CSC201", "CSC202", "CSC301"]))
            if username == "demo_student":
                self.student_record(user, first, last)

    def student_record(self, user, first, last):
        student, created = Student.objects.get_or_create(
            user=user,
            defaults={
                "first_name": first, "last_name": last,
                "matric_no": "VUG/CSC/24/99999",
                "email": "adaeze.okafor.demo@example.com",
                "phone": "+2348012345678",
                "dob": date(2005, 5, 12), "gender": "female",
                "address": "5 Nnamdi Azikiwe Road, Port Harcourt",
                "department": Department.objects.get(name="Computer Science"),
                "level": 200, "status": "active",
                "enrolled_on": date.today() - timedelta(days=200),
            },
        )
        Guardian.objects.get_or_create(
            student=student,
            defaults={"full_name": f"Chidi {last}", "relationship": "Father", "phone": "+2348087654321", "email": ""},
        )
        self.enroll(student, list(Course.objects.filter(department=student.department, level=student.level)))
        self.enroll(student, [Course.objects.get(code="ITE201")], previous_session())
        for enrollment in student.enrollments.filter(session=previous_session()):
            enrollment.grade = GRADES[enrollment.course_id % len(GRADES)]
            enrollment.save()

    def demo_passwords(self):
        # Never lock the demo accounts: reset them and clear the flag on every run.
        for username, password_var in [
            ("demo_admin", "DEMO_ADMIN_PASSWORD"), ("demo_staff", "DEMO_STAFF_PASSWORD"),
            ("demo_lecturer", "DEMO_LECTURER_PASSWORD"), ("demo_student", "DEMO_STUDENT_PASSWORD"),
        ]:
            user = User.objects.filter(username=username).first()
            if user:
                user.set_password(os.environ.get(password_var, DEMO_PASSWORDS[password_var]))
                user.save()
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.must_change_password = False
                profile.save()
