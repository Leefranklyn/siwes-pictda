from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from students.models import Student


class SeedDemoTests(TestCase):
    def test_idempotent_seeding(self):
        for _ in range(2):
            out = StringIO()
            call_command("seed_demo", stdout=out)
        self.assertEqual(Student.objects.count(), 61)
        graded = [student for student in Student.objects.all() if student.cgpa is not None]
        self.assertTrue(len(graded) >= 2)
        self.assertTrue(any(student.full_name == "Adaeze Okafor" for student in graded))
        self.assertTrue(Student.objects.filter(user__username="demo_student").exists())

    def test_demo_logins_work(self):
        call_command("seed_demo", stdout=StringIO())
        for username, password in [("demo_admin", "LocalAdmin20!"), ("demo_staff", "LocalStaff20!"), ("demo_student", "LocalStudent20!")]:
            with self.subTest(username=username):
                self.assertTrue(self.client.login(username=username, password=password))
