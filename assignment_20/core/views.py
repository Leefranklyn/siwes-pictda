from datetime import date
from types import SimpleNamespace

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import ListView

from accounts.mixins import AdminRequiredMixin, roles_required
from accounts.roles import ADMIN, STAFF
from students.forms import StudentForm
from students.models import Department, Student
from .models import AuditLog


def home(request):
    permissions = [
        ("View the dashboard", True, True, False),
        ("Search and open any student", True, True, False),
        ("Add, edit, and delete students", True, True, False),
        ("Manage enrollments and grades", True, True, False),
        ("See their own record", False, False, True),
        ("Manage courses, users, and the audit log", True, False, False),
    ]
    return render(request, "core/home.html", {"page_title": "Student Records", "public_layout": True, "permissions": permissions})


@roles_required(ADMIN, STAFF)
def dashboard(request):
    counts = Student.objects.aggregate(
        total=Count("pk"), active=Count("pk", filter=Q(status="active")),
        graduated=Count("pk", filter=Q(status="graduated")),
        inactive=Count("pk", filter=Q(status__in=["suspended", "withdrawn"])),
    )
    levels = dict(Student.objects.values_list("level").annotate(count=Count("pk")))
    statuses = dict(Student.objects.values_list("status").annotate(count=Count("pk")))
    return render(request, "core/dashboard.html", {
        "page_title": "Dashboard", "today": timezone.localdate(), "counts": counts,
        "levels": [{"label": label, "count": levels.get(level, 0), "share": round(levels.get(level, 0) * 100 / (counts["total"] or 1))} for level, label in Student.LEVELS],
        "statuses": [{"key": key, "label": label, "count": statuses.get(key, 0), "share": round(statuses.get(key, 0) * 100 / (counts["total"] or 1))} for key, label in Student.Status.choices],
        "activity": AuditLog.objects.select_related("actor")[:10],
    })


@roles_required(ADMIN, STAFF)
def charts_json(request):
    today = timezone.localdate()
    month_index = today.year * 12 + today.month - 1
    months = [date(index // 12, index % 12 + 1, 1) for index in range(month_index - 11, month_index + 1)]
    trend = Student.objects.filter(enrolled_on__gte=months[0], enrolled_on__lte=today).annotate(month=TruncMonth("enrolled_on")).values("month").annotate(count=Count("pk")).order_by("month")
    trend_counts = {row["month"].strftime("%Y-%m"): row["count"] for row in trend}
    departments = list(Department.objects.annotate(count=Count("students")).values("name", "count"))
    statuses = dict(Student.objects.values_list("status").annotate(count=Count("pk")))
    return JsonResponse({
        "departments": {"labels": [row["name"] for row in departments], "values": [row["count"] for row in departments]},
        "trend": {"labels": [month.strftime("%Y-%m") for month in months], "values": [trend_counts.get(month.strftime("%Y-%m"), 0) for month in months]},
        "status": {"labels": Student.Status.labels, "values": [statuses.get(status, 0) for status in Student.Status.values]},
    })


class AuditLogListView(AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = "core/audit_list.html"
    context_object_name = "logs"
    paginate_by = 25
    extra_context = {"page_title": "Audit log", "actions": AuditLog.ACTIONS, "models": ["Student", "Course", "Enrollment"]}

    def get_queryset(self):
        records = AuditLog.objects.select_related("actor")
        if self.request.GET.get("action") in dict(AuditLog.ACTIONS):
            records = records.filter(action=self.request.GET["action"])
        if self.request.GET.get("model") in self.extra_context["models"]:
            records = records.filter(model=self.request.GET["model"])
        return records


def styleguide(request):
    error_form = StudentForm(data={})
    error_form.is_valid()
    return render(request, "core/styleguide.html", {
        "page_title": "Styleguide", "public_layout": True, "form": StudentForm(), "error_form": error_form,
        "examples": [SimpleNamespace(pk=index, first_name="Adaeze", last_name="Okafor", photo=None, status=status, get_status_display=label) for index, (status, label) in enumerate(Student.Status.choices)],
    })


def permission_denied(request, exception):
    return render(request, "403.html", {"page_title": "Access denied"}, status=403)


def page_not_found(request, exception):
    return render(request, "404.html", {"page_title": "Page not found"}, status=404)
