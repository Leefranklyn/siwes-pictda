from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin, roles_required
from accounts.roles import ADMIN, STAFF, STUDENT, user_role
from .forms import CourseForm, EnrollmentForm, GuardianFormSet, StudentForm
from .models import Course, Department, Enrollment, Student


def student_records():
    return Student.objects.select_related("department").prefetch_related(
        "guardians", Prefetch("enrollments", queryset=Enrollment.objects.select_related("course"))
    )


class StudentListView(StaffRequiredMixin, ListView):
    model = Student
    context_object_name = "students"
    paginate_by = 10
    SORTS = {"name": ("last_name", "first_name"), "matric_no": ("matric_no",), "department": ("department__name",),
             "level": ("level",), "status": ("status",), "created_at": ("created_at",)}

    def get_template_names(self):
        return ["students/_table.html" if self.request.headers.get("HX-Request") else "students/student_list.html"]

    def get_queryset(self):
        params = self.request.GET
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
        self.sort = params.get("sort", "name")
        if self.sort.lstrip("-") not in self.SORTS or self.sort.startswith("--"):
            self.sort = "name"
        prefix = "-" if self.sort.startswith("-") else ""
        return records.order_by(*(prefix + field for field in self.SORTS[self.sort.lstrip("-")]), "pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Students", "departments": Department.objects.all(), "levels": Student.LEVELS,
            "statuses": Student.Status.choices, "sort": self.sort, "total_students": Student.objects.count(),
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
    year = timezone.localdate().year
    return {
        "student": student, "page_title": student.full_name,
        "enrollment_form": EnrollmentForm(student=student, initial={"session": f"{year - 1}/{year}"}),
        "cgpa": student.cgpa, "graded_count": len(student.graded_enrollments), **extra,
    }


class StudentDetailView(StaffRequiredMixin, DetailView):
    template_name = "students/student_detail.html"
    context_object_name = "student"

    def get_queryset(self):
        return student_records()

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), **detail_context(self.object)}


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
    return render(request, "students/student_detail.html", detail_context(student, enrollment_form=form))


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
    if user_role(request.user) in (ADMIN, STAFF):
        return redirect("core:dashboard")
    student = get_object_or_404(student_records(), user=request.user)
    return render(request, "students/student_detail.html", detail_context(student, readonly=True, page_title="My record"))


class CourseListView(AdminRequiredMixin, ListView):
    template_name = "students/course_list.html"
    context_object_name = "courses"
    queryset = Course.objects.select_related("department").annotate(student_count=Count("enrollments__student", distinct=True))
    extra_context = {"page_title": "Courses"}


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
