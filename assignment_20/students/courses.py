"""Course views: list, create, edit, detail with roster, enroll matching,
grade sheet, grade CSV import, roster export, and the lecturer home page."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin, roles_required
from accounts.roles import ADMIN, LECTURER, STAFF, can_grade, user_role
from core.exports import csv_response
from core.models import AuditLog, ImportBatch
from students.imports import ImportRejected, read_csv_file, validate_grade_rows
from students.models import Course, Department, Enrollment, Lecturer, Student
from students.utils import current_session
from .forms import CourseForm
from .models import Course, Department, Enrollment, Student


def course_queryset():
    return Course.objects.select_related("department").prefetch_related("lecturers")


def _sessions_for(courses):
    """Sessions that have enrollments for the given courses, newest first."""
    sessions = list(Enrollment.objects.filter(course__in=courses)
                    .values_list("session", flat=True).distinct().order_by("-session"))
    if current_session() not in sessions:
        sessions.insert(0, current_session())
    return sessions


def _visible_roster(course, session, user):
    """Enrollments for one course and session, restricted by role. For
    lecturers the query selects only the permitted student fields."""
    enrollments = (Enrollment.objects.filter(course=course, session=session)
                   .select_related("student", "student__department")
                   .order_by("student__matric_no"))
    if user_role(user) == LECTURER:
        enrollments = enrollments.only(
            "grade", "graded_at", "course",
            "student__first_name", "student__last_name", "student__matric_no",
            "student__level", "student__status", "student__department")
    return enrollments


class CourseListView(StaffRequiredMixin, ListView):
    """Course list. Admin and staff; lecturers use their own /teaching/ page."""
    template_name = "students/course_list.html"
    context_object_name = "courses"
    paginate_by = 12

    def get_template_names(self):
        return ["students/_course_table.html" if self.request.headers.get("HX-Request") else "students/course_list.html"]

    def get_queryset(self):
        courses = course_queryset().annotate(student_count=Count("enrollments__student", distinct=True))
        params = self.request.GET
        query = params.get("q", "").strip()
        if query:
            courses = courses.filter(Q(code__icontains=query) | Q(title__icontains=query))
        if params.get("department", "").isdecimal():
            courses = courses.filter(department_id=params["department"])
        if params.get("level") in {str(level) for level, label in Student.LEVELS}:
            courses = courses.filter(level=params["level"])
        if params.get("semester") in ("first", "second"):
            courses = courses.filter(semester=params["semester"])
        if params.get("unassigned") == "1":
            courses = courses.filter(lecturers__isnull=True)
        return courses.order_by("code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Courses", "departments": Department.objects.all(),
            "levels": Student.LEVELS, "can_edit": user_role(self.request.user) == ADMIN,
            "total_courses": Course.objects.count(),
        })
        return context




class CourseCreateView(AdminRequiredMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = "students/course_form.html"
    success_url = reverse_lazy("students:courses")
    extra_context = {"page_title": "Add course"}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Course added.")
        return response


class CourseUpdateView(AdminRequiredMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = "students/course_form.html"
    success_url = reverse_lazy("students:courses")
    extra_context = {"page_title": "Edit course"}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Changes saved.")
        return response


def _course_summary(enrollments):
    graded = [e for e in enrollments if e.grade]
    units = sum(e.course.credit_units for e in graded)
    average = round(sum(e.grade_points * e.course.credit_units for e in graded) / units, 1) if units else None
    distribution = {grade: 0 for grade in Enrollment.GRADE_POINTS}
    for enrollment in graded:
        distribution[enrollment.grade] += 1
    return {
        "enrolled": len(enrollments),
        "graded": len(graded),
        "pending": len(enrollments) - len(graded),
        "average": average,
        "distribution": distribution,
    }


@roles_required(ADMIN, STAFF, LECTURER)
def course_detail(request, pk):
    course = get_object_or_404(course_queryset(), pk=pk)
    role = user_role(request.user)
    if role == LECTURER and not course.lecturers.filter(user=request.user).exists():
        raise PermissionDenied
    session = request.GET.get("session") or current_session()
    roster = list(_visible_roster(course, session, request.user))
    context = {
        "page_title": course.code, "course": course, "session": session,
        "course_breadcrumb": [{"label": "Courses", "url": "/courses/"}, {"label": course.code}],
        "sessions": _sessions_for([course]), "roster": roster,
        "summary": _course_summary(roster),
        "can_grade": can_grade(request.user, course),
        "can_edit": role == ADMIN,
        "readonly_roster": role == LECTURER,
    }
    return render(request, "students/course_detail.html", context)


@roles_required(ADMIN, STAFF)
@require_POST
def enroll_matching(request, pk):
    course = get_object_or_404(Course, pk=pk)
    session = request.POST.get("session") or current_session()
    matching = list(course.students_matching)
    existing = set(Enrollment.objects.filter(course=course, session=session).values_list("student_id", flat=True))
    fresh = [student for student in matching if student.pk not in existing]
    with transaction.atomic():
        Enrollment.objects.bulk_create([
            Enrollment(student=student, course=course, session=session, semester=course.semester)
            for student in fresh
        ], ignore_conflicts=True)
        if fresh:
            AuditLog.objects.create(
                actor=request.user, action="create", model="Enrollment", object_id=course.pk,
                summary=f"Enrolled {len(fresh)} students in {course.code} for {session}",
                snapshot={"course": course.code, "session": session, "count": len(fresh)},
            )
    skipped = len(matching) - len(fresh)
    message = f"Enrolled {len(fresh)} students."
    if skipped:
        message += f" {skipped} were already enrolled."
    messages.success(request, message)
    return redirect("students:course_detail", pk=course.pk)


@roles_required(ADMIN, STAFF, LECTURER)
def grade_sheet(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not can_grade(request.user, course):
        raise PermissionDenied
    session = request.GET.get("session") or current_session()
    roster = list(_visible_roster(course, session, request.user))
    if request.method == "POST":
        changed = []
        with transaction.atomic():
            for enrollment in roster:
                grade = request.POST.get(f"grade_{enrollment.pk}", "").strip().upper() or None
                if grade and grade not in Enrollment.GRADE_POINTS:
                    continue
                if grade != enrollment.grade:
                    enrollment.grade = grade
                    enrollment.graded_at = timezone.now() if grade else None
                    enrollment.graded_by = request.user if grade else None
                    enrollment.save(update_fields=["grade", "graded_at", "graded_by"])
                    changed.append(enrollment)
        if changed:
            messages.success(request, f"Saved {len(changed)} grades.")
        else:
            messages.info(request, "No grades changed.")
        return redirect(f"{reverse('students:course_detail', args=[course.pk])}?session={session}")
    context = {
        "page_title": f"Grade sheet, {course.code}", "course": course, "session": session,
        "course_breadcrumb": [{"label": "Courses", "url": "/courses/"}, {"label": course.code, "url": f"/courses/{course.pk}/"}, {"label": "Grades"}],
        "sessions": _sessions_for([course]), "roster": roster,
        "graded_count": len([e for e in roster if e.grade]),
    }
    return render(request, "students/grade_sheet.html", context)


@roles_required(ADMIN, STAFF, LECTURER)
def grades_import(request, pk):
    """Grades by CSV: upload creates a preview batch, confirm applies it."""
    course = get_object_or_404(Course, pk=pk)
    if not can_grade(request.user, course):
        raise PermissionDenied
    session = request.POST.get("session") or request.GET.get("session") or current_session()
    batch = None
    if request.method == "POST" and request.FILES.get("file"):
        try:
            rows = read_csv_file(request.FILES["file"])
        except ImportRejected as problem:
            messages.error(request, str(problem))
        else:
            valid, errors = validate_grade_rows(course, session, rows)
            batch = ImportBatch.objects.create(
                kind="grades", uploaded_by=request.user, filename=request.FILES["file"].name,
                rows=[{"enrollment_id": item["enrollment"].pk, "matric_no": item["enrollment"].student.matric_no,
                       "name": item["enrollment"].student.full_name, "old_grade": item["enrollment"].grade,
                       "grade": item["grade"]} for item in valid],
                errors=errors, summary={"total": len(rows), "valid": len(valid), "invalid": len(errors)},
            )
            return redirect("students:grades_import_preview", pk=course.pk, batch_pk=batch.pk)
    return render(request, "students/grades_import.html", {
        "page_title": f"Import grades, {course.code}", "course": course, "session": session,
        "sessions": _sessions_for([course]),
    })


@roles_required(ADMIN, STAFF, LECTURER)
def grades_import_preview(request, pk, batch_pk):
    batch = get_object_or_404(ImportBatch, pk=batch_pk, kind="grades")
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST" and "confirm" in request.POST:
        if batch.status != "previewed":
            messages.error(request, "This import was already handled.")
            return redirect("students:course_detail", pk=course.pk)
        saved = 0
        with transaction.atomic():
            for row in batch.rows:
                enrollment = Enrollment.objects.filter(pk=row["enrollment_id"], course=course).first()
                if enrollment and row["grade"] != enrollment.grade:
                    enrollment.grade = row["grade"]
                    enrollment.graded_at = timezone.now() if row["grade"] else None
                    enrollment.graded_by = request.user if row["grade"] else None
                    enrollment.save(update_fields=["grade", "graded_at", "graded_by"])
                    saved += 1
        batch.rows = []
        batch.status = "confirmed"
        batch.summary.update({"created": 0, "updated": saved, "skipped": len(batch.errors)})
        batch.save()
        messages.success(request, f"Saved {saved} grades.")
        return redirect("students:course_detail", pk=course.pk)
    if request.method == "POST":
        batch.status = "discarded"
        batch.rows = []
        batch.save()
        return redirect("students:course_detail", pk=course.pk)
    return render(request, "students/import_preview.html", {
        "page_title": "Review grade import", "batch": batch, "course": course,
        "confirm_url": reverse("students:grades_import_preview", args=[course.pk, batch.pk]),
        "grade_import": True,
    })


@roles_required(ADMIN, STAFF, LECTURER)
def roster_csv(request, pk):
    from accounts.roles import can_grade

    course = get_object_or_404(Course, pk=pk)
    session = request.GET.get("session") or current_session()
    if not can_grade(request.user, course):
        raise PermissionDenied
    roster = _visible_roster(course, session, request.user)
    AuditLog.objects.create(
        actor=request.user, action="export", model="Course", object_id=course.pk,
        summary=f"Exported roster for {course.code} ({session})", snapshot={},
    )
    rows = ([e.student.matric_no, e.student.full_name, f"{e.student.level} level", e.grade or "Pending"]
            for e in roster)
    return csv_response(f"{course.code.replace('/', '-')}-roster",
                        ["matric_no", "name", "level", "grade"], rows)


@roles_required(ADMIN)
def course_import(request):
    """Courses by CSV: upload creates a preview batch, confirm applies it."""
    from students.imports import validate_course_rows

    if request.method == "POST" and request.FILES.get("file"):
        try:
            rows = read_csv_file(request.FILES["file"])
        except ImportRejected as problem:
            messages.error(request, str(problem))
        else:
            valid, errors = validate_course_rows(rows)
            batch = ImportBatch.objects.create(
                kind="courses", uploaded_by=request.user, filename=request.FILES["file"].name,
                rows=[{"line": item["line"], "code": item["code"], "title": item["title"],
                       "credit_units": item["credit_units"], "department": item["department"].name,
                       "level": item["level"], "semester": item["semester"],
                       "lecturers": [l.staff_number for l in item["lecturers"]]} for item in valid],
                errors=errors, summary={"total": len(rows), "valid": len(valid), "invalid": len(errors)},
            )
            return redirect("students:course_import_preview", pk=batch.pk)
    return render(request, "students/import_upload.html", {"page_title": "Import courses", "form": None, "course_import": True})


@roles_required(ADMIN)
def course_import_preview(request, pk):
    batch = get_object_or_404(ImportBatch, pk=pk, kind="courses")
    if request.method == "POST" and "confirm" in request.POST:
        if batch.status != "previewed":
            messages.error(request, "This import was already handled.")
            return redirect("students:courses")
        created = 0
        with transaction.atomic():
            for row in batch.rows:
                course, was_created = Course.objects.get_or_create(
                    code=row["code"],
                    defaults={"title": row["title"], "credit_units": row["credit_units"],
                              "department": Department.objects.get(name=row["department"]),
                              "level": row["level"], "semester": row["semester"]})
                if was_created:
                    created += 1
                    course.lecturers.set(Lecturer.objects.filter(staff_number__in=row["lecturers"]))
        batch.rows = []
        batch.status = "confirmed"
        batch.summary.update({"created": created, "skipped": len(batch.errors)})
        batch.save()
        AuditLog.objects.create(
            actor=request.user, action="import", model="Course", object_id=batch.pk,
            summary=f"Imported {created} courses from {batch.filename}", snapshot={"batch": batch.pk},
        )
        messages.success(request, f"Imported {created} courses.")
        return redirect("students:courses")
    if request.method == "POST":
        batch.status = "discarded"
        batch.rows = []
        batch.save()
        return redirect("students:courses")
    return render(request, "students/import_preview.html", {
        "page_title": "Review course import", "batch": batch, "course_import": True,
        "confirm_url": reverse("students:course_import_preview", args=[batch.pk]),
    })


@roles_required(ADMIN, STAFF, LECTURER)
def teaching(request):
    """Lecturer home: the courses they teach for a session."""
    lecturer = getattr(request.user, "lecturer", None)
    if not lecturer:
        raise PermissionDenied
    courses = list(lecturer.courses.all().order_by("code"))
    session = request.GET.get("session") or current_session()
    rows = []
    for course in courses:
        enrollments = _visible_roster(course, session, request.user)
        total = len(enrollments)
        graded = len([e for e in enrollments if e.grade])
        rows.append({"course": course, "students": total, "graded": graded, "percent": round(graded * 100 / total) if total else 0})
    return render(request, "students/teaching.html", {
        "page_title": "My courses", "rows": rows, "session": session,
        "sessions": _sessions_for(courses),
    })
