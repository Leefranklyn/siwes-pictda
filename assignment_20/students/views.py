import csv
import io
import json

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin, roles_required
from accounts.roles import ADMIN, LECTURER, STAFF, STUDENT, user_role
from core.exports import csv_response
from core.models import AuditLog, ImportBatch
from students.imports import (
    ImportRejected, create_students_from_import, read_csv_file, validate_student_csv,
)
from students.utils import current_session
from .forms import CourseForm, DepartmentForm, EnrollmentForm, GuardianFormSet, StudentForm
from .models import Course, Department, Enrollment, Guardian, Student


def student_records():
    return Student.objects.select_related("department", "user").prefetch_related(
        "guardians", Prefetch("enrollments", queryset=Enrollment.objects.select_related("course"))
    )


def filtered_students(params):
    """The student list query built from the request's search and filters.
    Shared by the list view and the CSV export."""
    records = student_records()
    query = params.get("q", "").strip()
    if query:
        records = records.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) |
                                 Q(email__icontains=query) | Q(matric_no__icontains=query))
    department = params.get("department", "")
    if department.isdecimal() and len(department) < 10:
        records = records.filter(department_id=int(department))
    if params.get("level") in {str(level) for level, label in Student.LEVELS}:
        records = records.filter(level=params["level"])
    if params.get("status") in Student.Status.values:
        records = records.filter(status=params["status"])
    return records


def sorted_students(params):
    sort = params.get("sort", "name")
    if sort.lstrip("-") not in StudentListView.SORTS or sort.startswith("--"):
        sort = "name"
    prefix = "-" if sort.startswith("-") else ""
    return filtered_students(params).order_by(
        *(prefix + field for field in StudentListView.SORTS[sort.lstrip("-")]), "pk"), sort


class StudentListView(StaffRequiredMixin, ListView):
    model = Student
    context_object_name = "students"
    paginate_by = 10
    SORTS = {"name": ("last_name", "first_name"), "matric_no": ("matric_no",), "department": ("department__name",),
             "level": ("level",), "status": ("status",), "created_at": ("created_at",)}

    def get_template_names(self):
        return ["students/_table.html" if self.request.headers.get("HX-Request") else "students/student_list.html"]

    def get_queryset(self):
        records, self.sort = sorted_students(self.request.GET)
        return records

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Students", "departments": Department.objects.all(), "levels": Student.LEVELS,
            "statuses": Student.Status.choices, "sort": self.sort, "total_students": Student.objects.count(),
            "status_counts": dict(Student.objects.values_list("status").annotate(count=Count("pk"))),
            "has_filters": any(self.request.GET.get(key) for key in ("q", "department", "level", "status")),
        })
        return context


class StudentFormViewMixin:
    model = Student
    form_class = StudentForm
    template_name = "students/student_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("guardians", GuardianFormSet(self.request.POST if self.request.method == "POST" else None, instance=self.object))
        context["page_title"] = "Edit student" if self.object else "Add student"
        return context

    def form_valid(self, form):
        guardians = GuardianFormSet(self.request.POST, instance=form.instance)
        if not guardians.is_valid():
            return self.render_to_response(self.get_context_data(form=form, guardians=guardians))
        created = self.object is None
        try:
            with transaction.atomic():
                self.object = form.save()
                guardians.instance = self.object
                guardians.save()
        except IntegrityError:
            form.add_error(None, "A student with this matric number or email already exists.")
            return self.render_to_response(self.get_context_data(form=form, guardians=guardians))
        messages.success(self.request, "Student added." if created else "Changes saved.")
        return redirect(self.object)


class StudentCreateView(StaffRequiredMixin, StudentFormViewMixin, CreateView):
    pass


class StudentUpdateView(StaffRequiredMixin, StudentFormViewMixin, UpdateView):
    pass


def detail_context(student, **extra):
    session = current_session()
    # Curriculum panel: courses that match the student, and which are registered.
    curriculum = Course.curriculum_for(student).select_related("department").prefetch_related("lecturers")
    registered = set(student.enrollments.filter(session=session).values_list("course_id", flat=True))
    carry_over = student.enrollments.select_related("course").filter(session=session, course__level__lt=student.level)
    context = {
        "student": student, "page_title": student.full_name,
        "enrollment_form": EnrollmentForm(student=student, initial={"session": session}),
        "cgpa": student.cgpa, "graded_count": len(student.graded_enrollments),
        "current_session": session, "curriculum": curriculum, "registered": registered,
        "carry_overs": carry_over,
        **extra,
    }
    context.setdefault("tab", "overview")
    return context


class StudentDetailView(StaffRequiredMixin, DetailView):
    template_name = "students/student_detail.html"
    context_object_name = "student"

    def get_queryset(self):
        return student_records()

    def get_context_data(self, **kwargs):
        student = self.object
        context = detail_context(student, staff_view=True)
        context["tab"] = self.request.GET.get("tab", "overview")
        context["breadcrumb"] = [{"label": "Students", "url": "/students/"}, {"label": student.full_name}]
        if context["tab"] == "history":
            context["history"] = AuditLog.objects.filter(
                model="Student", object_id=student.pk).select_related("actor")[:25]
        context["breadcrumb"] = [{"label": "Students", "url": "/students/"}, {"label": student.full_name}]
        return {**super().get_context_data(**kwargs), **context}


class StudentDeleteView(StaffRequiredMixin, DeleteView):
    model = Student
    template_name = "students/student_confirm_delete.html"
    success_url = reverse_lazy("students:list")
    extra_context = {"page_title": "Delete student"}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Student deleted.")
        return response


@roles_required(ADMIN, STAFF)
@require_POST
def enrollment_add(request, pk):
    student = get_object_or_404(student_records(), pk=pk)
    form = EnrollmentForm(request.POST, student=student)
    if form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(None, "This student is already enrolled in that course for this session.")
        else:
            messages.success(request, "Course added.")
            return redirect(student)
    return render(request, "students/student_detail.html", detail_context(student, enrollment_form=form, tab="courses"))


@roles_required(ADMIN, STAFF)
@require_POST
def enrollment_remove(request, pk, enrollment_pk):
    enrollment = get_object_or_404(Enrollment.objects.select_related("student", "course"), pk=enrollment_pk, student_id=pk)
    enrollment.delete()
    messages.success(request, "Course removed.")
    return redirect("students:detail", pk=pk)


@roles_required(ADMIN, STAFF)
def enrollment_edit(request, pk, enrollment_pk):
    enrollment = get_object_or_404(Enrollment.objects.select_related("student", "course"), pk=enrollment_pk, student_id=pk)
    form = EnrollmentForm(request.POST or None, instance=enrollment, student=enrollment.student)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(None, "This student is already enrolled in that course for this session.")
        else:
            messages.success(request, "Changes saved.")
            return redirect(enrollment.student)
    return render(request, "students/enrollment_form.html", {"form": form, "student": enrollment.student, "page_title": "Edit enrollment"})


@roles_required(ADMIN, STAFF, STUDENT)
def my_record(request):
    role = user_role(request.user)
    if role in (ADMIN, STAFF):
        return redirect("core:dashboard")
    if role == LECTURER:
        return redirect("students:teaching")
    student = get_object_or_404(student_records(), user=request.user)
    context = detail_context(student, readonly=True, page_title="My record")
    context["tab"] = request.GET.get("tab", "overview")
    return render(request, "students/student_detail.html", context)


# ---------------------------------------------------------------------------
# Curriculum registration
# ---------------------------------------------------------------------------

@roles_required(ADMIN, STAFF)
@require_POST
def register_all(request, pk):
    """Enroll the student in every missing curriculum course for the session."""
    student = get_object_or_404(Student, pk=pk)
    session = request.POST.get("session") or current_session()
    curriculum = Course.curriculum_for(student)
    existing = set(student.enrollments.filter(session=session).values_list("course_id", flat=True))
    fresh = [course for course in curriculum if course.pk not in existing]
    with transaction.atomic():
        Enrollment.objects.bulk_create([
            Enrollment(student=student, course=course, session=session, semester=course.semester)
            for course in fresh
        ], ignore_conflicts=True)
    messages.success(request, f"Registered {len(fresh)} courses for {session}.")
    return redirect("students:detail", pk=pk)


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

class DepartmentListView(AdminRequiredMixin, ListView):
    template_name = "students/department_list.html"
    context_object_name = "departments"
    queryset = Department.objects.annotate(
        student_count=Count("students"), course_count=Count("courses", distinct=True),
        lecturer_count=Count("lecturers", distinct=True))
    extra_context = {"page_title": "Departments"}


class DepartmentCreateView(AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = "students/department_form.html"
    success_url = reverse_lazy("students:departments")
    extra_context = {"page_title": "Add department", "breadcrumb": [{"label": "Departments", "url": "/departments/"}, {"label": "Add"}]}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Department created.")
        return response


class DepartmentUpdateView(AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = "students/department_form.html"
    success_url = reverse_lazy("students:departments")
    extra_context = {"page_title": "Edit department", "breadcrumb": [{"label": "Departments", "url": "/departments/"}, {"label": "Edit"}]}

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Department updated.")
        return response


class DepartmentDeleteView(AdminRequiredMixin, DeleteView):
    model = Department
    template_name = "students/department_confirm_delete.html"
    success_url = reverse_lazy("students:departments")
    extra_context = {"page_title": "Delete department", "breadcrumb": [{"label": "Departments", "url": "/departments/"}, {"label": "Delete"}]}

    def has_in_use(self):
        department = self.get_object()
        return {
            "students": department.students.count(),
            "courses": department.courses.count(),
            "lecturers": department.lecturers.count(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["counts"] = self.has_in_use()
        return context

    def post(self, request, *args, **kwargs):
        # PROTECT on the foreign keys raises ProtectedError when in use; the
        # view never deletes a department that other records point at.
        from django.db.models import ProtectedError

        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, "This department is still in use. Move or remove these first.")
            return redirect("students:department_delete", pk=self.get_object().pk)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Department deleted.")
        return response


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

@roles_required(ADMIN, STAFF)
def students_export(request):
    """CSV export of the student list, honoring the current search and filters."""
    records = filtered_students(request.GET)
    AuditLog.objects.create(
        actor=request.user, action="export", model="Student", object_id=0,
        summary=f"Exported {records.count()} students", snapshot={},
    )
    rows = ([s.matric_no, s.first_name, s.last_name, s.email, s.phone, s.department.name,
             s.level, s.status, s.enrolled_on, s.cgpa if s.cgpa is not None else ""] for s in records)
    return csv_response("students",
                        ["matric_no", "first_name", "last_name", "email", "phone",
                         "department", "level", "status", "enrolled_on", "cgpa"], rows)


# ---------------------------------------------------------------------------
# Bulk actions
# ---------------------------------------------------------------------------

MAX_BULK_IDS = 500


def _selected_ids(request):
    raw = json.loads(request.POST.get("ids", "[]"))
    if not isinstance(raw, list):
        return []
    return [int(value) for value in raw if str(value).isdecimal()][:MAX_BULK_IDS]


@roles_required(ADMIN, STAFF)
@require_POST
def bulk_promote(request):
    ids = _selected_ids(request)
    promoted, capped = 0, 0
    students = Student.objects.filter(pk__in=ids)
    if len(ids) <= 100:
        # Small batches: save one by one so the audit log gets an entry each.
        with transaction.atomic():
            for student in students:
                if student.level >= 500:
                    capped += 1
                    continue
                student.level += 100
                student.save(update_fields=["level"])
                promoted += 1
                AuditLog.objects.create(
                    actor=request.user, action="update", model="Student", object_id=student.pk,
                    summary=f"Promoted {student.matric_no} to {student.level} level", snapshot={},
                )
    else:
        for student in students:
            if student.level >= 500:
                capped += 1
                continue
            student.level += 100
            promoted += 1
        with transaction.atomic():
            Student.objects.bulk_update(students, ["level"])
            AuditLog.objects.create(
                actor=request.user, action="update", model="Student", object_id=0,
                summary=f"Promoted {promoted} students in bulk", snapshot={"ids": ids[:50]},
            )
    message = f"Promoted {promoted} students."
    if capped:
        message += f" {capped} at 500 level were not changed."
    messages.success(request, message)
    return redirect("students:list")


@roles_required(ADMIN, STAFF)
@require_POST
def bulk_status(request):
    ids = _selected_ids(request)
    status = request.POST.get("status", "")
    if status not in Student.Status.values:
        messages.error(request, "Choose a valid status.")
        return redirect("students:list")
    with transaction.atomic():
        for student in Student.objects.filter(pk__in=ids):
            student.status = status
            student.save(update_fields=["status"])
            AuditLog.objects.create(
                actor=request.user, action="update", model="Student", object_id=student.pk,
                summary=f"Set status of {student.matric_no} to {student.get_status_display()}", snapshot={},
            )
    messages.success(request, f"Changed status for {len(ids)} students.")
    return redirect("students:list")


# ---------------------------------------------------------------------------
# Transcripts
# ---------------------------------------------------------------------------

def _transcript_context(student):
    """Group the student's enrollments by session and semester, newest first."""
    enrollments = student.enrollments.select_related("course").order_by("-session", "course__code")
    sessions = {}
    for enrollment in enrollments:
        sessions.setdefault(enrollment.session, {}).setdefault(enrollment.semester, []).append(enrollment)
    from students.utils import session_gpa, units_summary

    period_rows = []
    for session, semesters in sorted(sessions.items(), reverse=True):
        for semester, rows in semesters.items():
            gpa = session_gpa(rows)
            attempted, earned = units_summary(rows)
            period_rows.append({
                "session": session, "semester": semester, "rows": rows,
                "gpa": gpa, "attempted": attempted, "earned": earned,
            })
    attempted, earned = units_summary(enrollments)
    return {"student": student, "periods": period_rows, "attempted": attempted, "earned": earned,
            "cgpa": student.cgpa, "today": timezone.localdate()}


@roles_required(ADMIN, STAFF)
def transcript(request, pk):
    student = get_object_or_404(student_records(), pk=pk)
    context = _transcript_context(student)
    context.update({"page_title": f"Transcript, {student.full_name}"})
    return render(request, "students/transcript.html", context)


@roles_required(ADMIN, STAFF, STUDENT)
def my_transcript(request):
    if user_role(request.user) != STUDENT:
        raise PermissionDenied
    student = get_object_or_404(student_records(), user=request.user)
    context = _transcript_context(student)
    context.update({"page_title": "My transcript"})
    return render(request, "students/transcript.html", context)


# ---------------------------------------------------------------------------
# Students by CSV
# ---------------------------------------------------------------------------

CREDENTIALS_SESSION_KEY = "import_credentials"


@roles_required(ADMIN, STAFF)
def students_import(request):
    from .forms import StudentImportForm

    form = StudentImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            rows = read_csv_file(request.FILES["file"])
        except ImportRejected as problem:
            form.add_error("file", str(problem))
        else:
            request.FILES["file"].seek(0)
            valid, errors = validate_student_csv(rows)
            batch = ImportBatch.objects.create(
                kind="students", uploaded_by=request.user, filename=request.FILES["file"].name,
                rows=valid, errors=errors,
                summary={"total": len(rows), "valid": len(valid), "invalid": len(errors),
                         "create_logins": form.cleaned_data["create_logins"],
                         "skip_errors": form.cleaned_data["skip_errors"]},
            )
            return redirect("students:import_preview", pk=batch.pk)
    return render(request, "students/import_upload.html", {"page_title": "Import students", "form": form})


@roles_required(ADMIN, STAFF)
def students_import_preview(request, pk):
    batch = get_object_or_404(ImportBatch, pk=pk, kind="students")
    if request.method == "POST" and "confirm" in request.POST:
        if batch.status != "previewed":
            messages.error(request, "This import was already handled.")
            return redirect("students:import_history")
        if batch.errors and not batch.summary.get("skip_errors"):
            messages.error(request, "Fix the errors or choose to skip rows with errors.")
            return redirect("students:import_preview", pk=batch.pk)
        try:
            with transaction.atomic():
                students, credentials = create_students_from_import(
                    batch.rows, create_logins=batch.summary.get("create_logins", False))
        except Exception:
            messages.error(request, "The import failed and nothing was written.")
            return redirect("students:import_preview", pk=batch.pk)
        batch.rows = []
        batch.status = "confirmed"
        batch.summary.update({"created": len(students), "skipped": len(batch.errors)})
        batch.save()
        AuditLog.objects.create(
            actor=request.user, action="import", model="Student", object_id=batch.pk,
            summary=f"Imported {len(students)} students from {batch.filename}",
            snapshot={"batch": batch.pk, "created": len(students)},
        )
        if credentials:
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["username", "temporary_password"])
            for credential in credentials:
                writer.writerow([credential["username"], credential["password"]])
            request.session[CREDENTIALS_SESSION_KEY] = buffer.getvalue()
        messages.success(request, f"Imported {len(students)} students.")
        return render(request, "students/import_done.html", {
            "page_title": "Import complete", "batch": batch,
            "created": len(students), "skipped": len(batch.errors),
            "has_credentials": bool(credentials),
        })
    if request.method == "POST":
        batch.status = "discarded"
        batch.rows = []
        batch.save()
        return redirect("students:import_history")
    return render(request, "students/import_preview.html", {
        "page_title": "Review import", "batch": batch,
        "confirm_url": reverse("students:import_preview", args=[batch.pk]),
    })


@roles_required(ADMIN, STAFF)
def students_import_credentials(request, pk):
    """One-time download of the credentials CSV from the session."""
    batch = get_object_or_404(ImportBatch, pk=pk, kind="students")
    content = request.session.pop(CREDENTIALS_SESSION_KEY, None)
    if not content:
        messages.error(request, "The credentials download is no longer available.")
        return redirect("students:import_history")
    response = HttpResponse(content, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="logins-{batch.pk}.csv"'
    return response


@roles_required(ADMIN, STAFF)
def students_import_errors_csv(request, pk):
    """Download the validation errors of one batch as CSV."""
    batch = get_object_or_404(ImportBatch, pk=pk)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="import-{batch.pk}-errors.csv"'
    writer = csv.writer(response)
    writer.writerow(["row", "field", "message"])
    for error in batch.errors:
        writer.writerow([error.get("row"), error.get("field"), error.get("message")])
    return response


@roles_required(ADMIN, STAFF)
def students_import_history(request):
    batches = ImportBatch.objects.filter(kind="students").select_related("uploaded_by")
    return render(request, "students/import_history.html", {"page_title": "Import history", "batches": batches})


@roles_required(ADMIN, STAFF)
def students_import_template(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students-template.csv"'
    writer = csv.writer(response)
    writer.writerow(["first_name", "last_name", "email", "matric_no", "department", "level",
                     "dob", "gender", "phone", "address", "status", "enrolled_on",
                     "guardian_name", "guardian_relationship", "guardian_phone", "guardian_email"])
    writer.writerow(["Fatima", "Abubakar", "fatima.abubakar@example.com", "VUG/CSC/24/20001",
                     "Computer Science", "200", "2005-03-14", "female", "+2348012345601",
                     "14 Ahmadu Bello Way, Zaria", "active", "2025-09-20",
                     "Halima Abubakar", "Mother", "+2348012345611", ""])
    writer.writerow(["Nnamdi", "Obi", "nnamdi.obi@example.com", "VUG/CSC/24/20002",
                     "Computer Science", "200", "2005-07-02", "male", "+2348012345602",
                     "", "active", "2025-09-20", "", "", "", ""])
    return response
