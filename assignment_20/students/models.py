from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone


phone_validator = RegexValidator(
    r"^\+?[0-9]{7,19}$",
    "Enter a valid phone number, digits only, with an optional leading +.",
)
matric_validator = RegexValidator(r"^[A-Z]+/[A-Z]+/[0-9]{2}/[0-9]{5}$", "Use the format VUG/CSC/24/10001.")


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        GRADUATED = "graduated", "Graduated"
        SUSPENDED = "suspended", "Suspended"
        WITHDRAWN = "withdrawn", "Withdrawn"

    LEVELS = [(level, f"{level} level") for level in (100, 200, 300, 400, 500)]
    GENDERS = [("male", "Male"), ("female", "Female"), ("other", "Other")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="student")
    matric_no = models.CharField(max_length=30, validators=[matric_validator])
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=20, validators=[phone_validator])
    dob = models.DateField("Date of birth")
    gender = models.CharField(max_length=10, choices=GENDERS)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to="students/photos/", null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="students")
    level = models.PositiveSmallIntegerField(choices=LEVELS)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    enrolled_on = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(Lower("matric_no"), name="uniq_student_matric_ci"),
            models.UniqueConstraint(Lower("email"), name="uniq_student_email_ci"),
        ]
        indexes = [models.Index(fields=["status", "level"]), models.Index(fields=["enrolled_on"]), models.Index(fields=["-created_at"])]

    def clean(self):
        super().clean()
        self.matric_no = self.matric_no.strip().upper()
        self.email = self.email.strip().lower()
        if self.dob and self.dob > timezone.localdate():
            raise ValidationError({"dob": "Date of birth cannot be in the future."})

    def save(self, *args, **kwargs):
        self.matric_no = self.matric_no.strip().upper()
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def graded_enrollments(self):
        if "enrollments" in getattr(self, "_prefetched_objects_cache", {}):
            return [enrollment for enrollment in self.enrollments.all() if enrollment.grade]
        return list(self.enrollments.exclude(grade__isnull=True).exclude(grade="").select_related("course"))

    @property
    def cgpa(self):
        graded = self.graded_enrollments
        units = sum(enrollment.course.credit_units for enrollment in graded)
        if not units:
            return None
        points = sum(Enrollment.GRADE_POINTS[enrollment.grade] * enrollment.course.credit_units for enrollment in graded)
        return round(points / units, 2)

    def get_absolute_url(self):
        return reverse("students:detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.matric_no})"


class Guardian(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="guardians")
    full_name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.full_name


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150)
    credit_units = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="courses")

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code}: {self.title}"


class Enrollment(models.Model):
    GRADE_POINTS = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="enrollments")
    session = models.CharField(max_length=9, validators=[RegexValidator(r"^[0-9]{4}/[0-9]{4}$", "Use the format 2025/2026.")])
    semester = models.CharField(max_length=6, choices=[("first", "First"), ("second", "Second")])
    grade = models.CharField(max_length=1, choices=[(grade, grade) for grade in GRADE_POINTS], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-session", "course__code"]
        constraints = [models.UniqueConstraint(fields=["student", "course", "session"], name="uniq_student_course_session")]

    def __str__(self):
        return f"{self.student.matric_no}, {self.course.code}, {self.session}"
