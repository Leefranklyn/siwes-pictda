"""CSV parsing and validation for the bulk imports.

Everything here is plain functions: parse a file, validate rows, create the
records. The views in students/views.py call these, show the preview, and
confirm.
"""
import csv
import io
import re
import secrets
from datetime import date, datetime

from django.core.validators import RegexValidator
from django.utils import timezone

from students.models import Course, Department, Enrollment, Guardian, Lecturer, Student

MAX_IMPORT_ROWS = 1000
MAX_IMPORT_BYTES = 2 * 1024 * 1024
PHONE_VALIDATOR = RegexValidator(r"^\+?[0-9]{7,19}$", "Enter a valid phone number, digits only, with an optional leading +.")
MATRIC_RE = re.compile(r"^[A-Z]+/[A-Z]+/[0-9]{2}/[0-9]{5}$")
STATUSES = {value for value, label in Student.Status.choices}
GENDERS = {value for value, label in Student.GENDERS}


class ImportRejected(Exception):
    """Raised when the file itself cannot be processed at all."""


def read_csv_file(django_file):
    """Decode and parse an uploaded CSV into a list of dicts keyed by header.
    Raises ImportRejected for wrong type, size, or encoding."""
    data = django_file.read()
    if len(data) > MAX_IMPORT_BYTES:
        raise ImportRejected("The file is larger than 2 MB.")
    if b"\x00" in data[:1024]:
        raise ImportRejected("That does not look like a CSV text file.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ImportRejected("The file must be UTF-8 CSV text.")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for index, raw in enumerate(reader, start=2):  # line 1 is the header
        row = {key.strip().lower(): (value or "").strip() for key, value in raw.items() if key}
        row["line"] = index
        rows.append(row)
    if len(rows) > MAX_IMPORT_ROWS:
        raise ImportRejected(f"The file has more than {MAX_IMPORT_ROWS} rows.")
    return rows


def parse_date(value):
    """YYYY-MM-DD or DD/MM/YYYY, or None with a message."""
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    return None


def validate_student_row(row, seen_emails, seen_matrics):
    """Validate one CSV row. Returns (cleaned, errors) where errors is a list
    of {field, message} dicts."""
    errors = []

    def require(field, label):
        value = row.get(field, "")
        if not value:
            errors.append({"field": field, "message": f"{label} is required."})
        return value

    first_name = require("first_name", "First name")
    last_name = require("last_name", "Last name")
    email = row.get("email", "").strip().lower()
    matric = row.get("matric_no", "").strip().upper()
    department = row.get("department", "")
    level_raw = row.get("level", "")
    dob_raw = row.get("dob", "")
    gender = row.get("gender", "").strip().lower()
    phone = row.get("phone", "").strip()

    if email:
        if "@" not in email or "." not in email.split("@")[-1]:
            errors.append({"field": "email", "message": "Enter a valid email address."})
        elif email in seen_emails or Student.objects.filter(email__iexact=email).exists():
            where = "this file" if email in seen_emails else "the database"
            errors.append({"field": "email", "message": f"Email already exists in {where}."})
        seen_emails.add(email)

    if matric:
        if not MATRIC_RE.match(matric):
            errors.append({"field": "matric_no", "message": "Use the format VUG/CSC/24/10001."})
        elif matric in seen_matrics or Student.objects.filter(matric_no__iexact=matric).exists():
            where = "this file" if matric in seen_matrics else "the database"
            errors.append({"field": "matric_no", "message": f"Matric number already exists in {where}."})
        seen_matrics.add(matric)

    department_obj = Department.objects.filter(name__iexact=department).first() if department else None
    if not department_obj:
        errors.append({"field": "department", "message": "No department with that name."})

    level = None
    digits = re.sub(r"[^0-9]", "", level_raw)
    if digits and int(digits) in (100, 200, 300, 400, 500):
        level = int(digits)
    else:
        errors.append({"field": "level", "message": "Level must be 100 to 500."})

    dob = parse_date(dob_raw) if dob_raw else None
    if not dob:
        errors.append({"field": "dob", "message": "Date of birth must be YYYY-MM-DD or DD/MM/YYYY."})
    elif dob > timezone.localdate():
        errors.append({"field": "dob", "message": "Date of birth cannot be in the future."})

    if gender not in GENDERS:
        errors.append({"field": "gender", "message": "Gender must be male, female, or other."})

    if phone:
        try:
            PHONE_VALIDATOR(phone)
        except Exception:
            errors.append({"field": "phone", "message": "Enter a valid phone number, digits only, with an optional leading +."})
    else:
        errors.append({"field": "phone", "message": "Phone is required."})

    status = row.get("status", "active").strip().lower() or "active"
    if status not in STATUSES:
        errors.append({"field": "status", "message": "Status must be active, graduated, suspended, or withdrawn."})

    enrolled_on = parse_date(row.get("enrolled_on", "")) if row.get("enrolled_on") else timezone.localdate()

    guardian_name = row.get("guardian_name", "").strip()
    guardian = None
    if guardian_name:
        guardian_phone = row.get("guardian_phone", "").strip()
        if not row.get("guardian_relationship", "").strip():
            errors.append({"field": "guardian_relationship", "message": "Guardian relationship is required when a guardian is given."})
        if not guardian_phone:
            errors.append({"field": "guardian_phone", "message": "Guardian phone is required when a guardian is given."})
        guardian = {
            "full_name": guardian_name,
            "relationship": row.get("guardian_relationship", "").strip(),
            "phone": guardian_phone,
            "email": row.get("guardian_email", "").strip(),
        }

    if errors:
        return None, errors
    cleaned = {
        "line": row.get("line"),
        "first_name": first_name, "last_name": last_name, "email": email, "matric_no": matric,
        "department_id": department_obj.pk, "level": level, "dob": dob.isoformat(),
        "gender": gender, "phone": phone, "address": row.get("address", ""),
        "status": status, "enrolled_on": enrolled_on.isoformat(),
        "guardian": guardian,
    }
    return cleaned, []


def validate_student_csv(rows):
    """Validate every row. Returns (valid, errors) where errors is a list of
    {row, field, message} for the preview table."""
    seen_emails, seen_matrics = set(), set()
    valid, errors = [], []
    for row in rows:
        cleaned, row_errors = validate_student_row(row, seen_emails, seen_matrics)
        if cleaned:
            valid.append(cleaned)
        for error in row_errors:
            errors.append({"row": row.get("line"), "field": error["field"], "message": error["message"]})
    return valid, errors


def create_students_from_import(valid, create_logins=False):
    """Create the students and their guardians in bulk. Caller wraps in
    transaction.atomic(). Returns (created_students, credentials) where
    credentials holds one {username, password} per created login."""
    students = Student.objects.bulk_create([
        Student(
            first_name=row["first_name"], last_name=row["last_name"], email=row["email"],
            matric_no=row["matric_no"], department_id=row["department_id"], level=row["level"],
            dob=row["dob"], gender=row["gender"], phone=row["phone"], address=row["address"],
            status=row["status"], enrolled_on=row["enrolled_on"],
        ) for row in valid
    ])
    Guardian.objects.bulk_create([
        Guardian(student=student, **row["guardian"])
        for student, row in zip(students, valid) if row["guardian"]
    ])
    credentials = []
    if create_logins:
        from django.contrib.auth.models import User

        for student in students:
            username = student.matric_no.lower().replace("/", "-")
            password = "Stu" + secrets.token_urlsafe(8).replace("-", "a").replace("_", "b")[:7] + "1!"
            user = User.objects.create_user(username, password=password, first_name=student.first_name, last_name=student.last_name)
            user.profile.must_change_password = True
            user.profile.save()
            student.user = user
            credentials.append({"username": username, "password": password})
        Student.objects.bulk_update(students, ["user"])
    return students, credentials


def validate_grade_rows(course, session, rows):
    """Validate grade rows for one course and session. Returns (valid, errors).
    Each valid item is {enrollment, grade}."""
    from students.utils import current_session

    session = session or current_session()
    enrollments = {e.student.matric_no.upper(): e for e in Enrollment.objects.filter(course=course, session=session).select_related("student")}
    valid, errors = [], []
    seen_matrics = set()
    for row in rows:
        line = row.get("line")
        matric = row.get("matric_no", "").strip().upper()
        grade = row.get("grade", "").strip().upper()
        if not matric:
            errors.append({"row": line, "field": "matric_no", "message": "Matric number is required."})
            continue
        if matric in seen_matrics:
            errors.append({"row": line, "field": "matric_no", "message": "Matric number appears twice in this file."})
            continue
        seen_matrics.add(matric)
        enrollment = enrollments.get(matric)
        if not enrollment:
            errors.append({"row": line, "field": "matric_no", "message": "Not enrolled in this course for the session."})
            continue
        if grade and grade not in Enrollment.GRADE_POINTS:
            errors.append({"row": line, "field": "grade", "message": "Grade must be A to F or blank."})
            continue
        valid.append({"enrollment": enrollment, "grade": grade or None})
    return valid, errors


def validate_course_rows(rows):
    """Validate course rows for the course CSV import. Returns (valid, errors)."""
    valid, errors = [], []
    seen_codes = set()
    for row in rows:
        line = row.get("line")
        row_errors = []

        def check(condition, field, message):
            if not condition:
                row_errors.append({"row": line, "field": field, "message": message})

        code = row.get("code", "").strip().upper()
        title = row.get("title", "").strip()
        units = re.sub(r"[^0-9]", "", row.get("credit_units", ""))
        department = Department.objects.filter(name__iexact=row.get("department", "")).first()
        level = re.sub(r"[^0-9]", "", row.get("level", ""))
        semester = row.get("semester", "").strip().lower()

        check(bool(re.match(r"^[A-Z]{2,4}[0-9]{3}$", code)), "code", "Use a code like CSC201.")
        if code in seen_codes:
            check(False, "code", "Course code appears twice in this file.")
        elif Course.objects.filter(code__iexact=code).exists():
            check(False, "code", "Course code already exists in the database.")
        seen_codes.add(code)
        check(bool(title), "title", "Title is required.")
        check(bool(units) and 1 <= int(units or 0) <= 6, "credit_units", "Credit units must be 1 to 6.")
        check(bool(department), "department", "No department with that name.")
        check(level in ("100", "200", "300", "400", "500"), "level", "Level must be 100 to 500.")
        check(semester in ("first", "second"), "semester", "Semester must be first or second.")

        lecturers = []
        for number in [part.strip().upper() for part in row.get("lecturer_staff_numbers", "").split(";") if part.strip()]:
            lecturer = Lecturer.objects.filter(staff_number__iexact=number).first()
            if not lecturer:
                row_errors.append({"row": line, "field": "lecturer_staff_numbers", "message": f"No lecturer with staff number {number}."})
            else:
                lecturers.append(lecturer)

        if row_errors:
            errors.extend(row_errors)
            continue
        valid.append({
            "line": line, "code": code, "title": title, "credit_units": int(units),
            "department": department, "level": int(level), "semester": semester,
            "lecturers": lecturers,
        })
    return valid, errors
