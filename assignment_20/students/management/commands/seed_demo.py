import os
import random
from datetime import date, timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from students.models import Course, Department, Enrollment, Guardian, Student

FIRST_NAMES = ["Adaeze", "Chinedu", "Fatima", "Ibrahim", "Kelechi", "Ngozi", "Olumide", "Aisha", "Emeka", "Zainab",
               "Tunde", "Chiamaka", "Yusuf", "Amara", "Obinna", "Halima", "Segun", "Uchenna", "Bola", "Ifeanyi",
               "Amina", "Damilola", "Nnamdi", "Funmilayo", "Ekene", "Rukayat", "Ogbemudia", "Chisom", "Musa", "Tomilayo"]
LAST_NAMES = ["Okafor", "Balogun", "Abubakar", "Eze", "Adeyemi", "Olawale", "Musa", "Nwosu", "Okonkwo", "Bello",
              "Ogunleye", "Umeh", "Aliyu", "Obi", "Adeola", "Danjuma", "Onyeka", "Sadiq", "Lawal", "Igwelo"]
RELATIONSHIPS = ["Mother", "Father", "Aunt", "Uncle", "Elder sister", "Elder brother"]
STATUSES = ["active"] * 7 + ["graduated", "suspended", "withdrawn"]
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
DEMO_PASSWORDS = {"DEMO_ADMIN_PASSWORD": "LocalAdmin20!", "DEMO_STAFF_PASSWORD": "LocalStaff20!", "DEMO_STUDENT_PASSWORD": "LocalStudent20!"}


class Command(BaseCommand):
    help = "Create idempotent demo data: departments, courses, students, guardians, enrollments, groups, and demo users."

    def handle(self, *args, **options):
        random.seed(20)
        self.departments()
        self.courses()
        self.students()
        self.users()
        self.stdout.write("Demo data is ready.")

    def departments(self):
        for name in DEPARTMENTS:
            Department.objects.get_or_create(name=name)

    def courses(self):
        for index, (code, title, units) in enumerate(COURSE_SEED):
            department = Department.objects.get(name=DEPARTMENTS[index % len(DEPARTMENTS)])
            Course.objects.get_or_create(code=code, defaults={"title": title, "credit_units": units, "department": department})

    def students(self):
        courses = list(Course.objects.all())
        today = date.today()
        for index in range(30):
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
                    "email": f"{first.lower()}.{last.lower()}@example.com",
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
            self.enroll(student, random.sample(courses, random.randint(3, 6)))
        for matric in self.graded_matrics:
            student = Student.objects.get(matric_no=matric)
            for enrollment in student.enrollments.all()[:3]:
                if not enrollment.grade:
                    enrollment.grade = GRADES[enrollment.course_id % len(GRADES)]
                    enrollment.save()

    def enroll(self, student, chosen):
        for course in chosen:
            Enrollment.objects.get_or_create(
                student=student, course=course, session="2025/2026",
                defaults={"semester": ["first", "second"][course.pk % 2], "grade": None},
            )

    def users(self):
        for group_name in ("Admin", "Staff"):
            Group.objects.get_or_create(name=group_name)
        accounts = [
            ("demo_admin", "Demo", "Admin", "Admin", "DEMO_ADMIN_PASSWORD"),
            ("demo_staff", "Demo", "Staff", "Staff", "DEMO_STAFF_PASSWORD"),
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
        self.enroll(student, Course.objects.filter(code__in=["CSC101", "CSC102", "CSC201", "ITE301"]))
        for enrollment in student.enrollments.all()[:3]:
            if not enrollment.grade:
                enrollment.grade = GRADES[enrollment.course_id % len(GRADES)]
                enrollment.save()

    @property
    def graded_matrics(self):
        if not hasattr(self, "_graded_matrics"):
            self._graded_matrics = set(Student.objects.order_by("matric_no").values_list("matric_no", flat=True)[:2])
        return self._graded_matrics
