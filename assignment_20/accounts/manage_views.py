"""Admin-only account management: list, create, edit, reset, deactivate."""
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import AccountForm, generate_temporary_password
from accounts.mixins import roles_required
from accounts.roles import ADMIN, user_role
from core.models import AuditLog
from students.models import Lecturer, Student

ROLE_GROUPS = {"admin": "Admin", "staff": "Staff", "lecturer": "Lecturer"}
SESSION_CREDENTIALS_KEY = "one_time_credentials"


def _role_label(user):
    return user_role(user) or "none"


def _linked_record(user):
    if hasattr(user, "student"):
        return user.student
    if hasattr(user, "lecturer"):
        return user.lecturer
    return None


def _last_active_admin_exists(exclude_user):
    admins = User.objects.filter(groups__name="Admin", is_active=True).exclude(pk=exclude_user.pk)
    return admins.exists()


@roles_required(ADMIN)
def account_list(request):
    query = request.GET.get("q", "").strip()
    role_filter = request.GET.get("role", "")
    users = User.objects.select_related("profile", "student", "lecturer").prefetch_related("groups").order_by("username")
    if query:
        users = users.filter(
            Q(username__icontains=query) | Q(email__icontains=query) |
            Q(first_name__icontains=query) | Q(last_name__icontains=query))
    if role_filter in ("admin", "staff", "lecturer", "student"):
        if role_filter == "student":
            users = users.filter(student__isnull=False)
        else:
            users = users.filter(groups__name=ROLE_GROUPS[role_filter])
    counts = {
        "all": User.objects.count(),
        "admin": User.objects.filter(groups__name="Admin").count(),
        "staff": User.objects.filter(groups__name="Staff").count(),
        "lecturer": User.objects.filter(groups__name="Lecturer").count(),
        "student": User.objects.filter(student__isnull=False).count(),
    }
    page_obj = Paginator(users, 15).get_page(request.GET.get("page"))
    rows = [{
        "user": user,
        "role": _role_label(user),
        "record": _linked_record(user),
        "active": user.is_active,
    } for user in page_obj.object_list]
    # One-time credentials from create/reset are shown once and then dropped.
    credentials = request.session.pop(SESSION_CREDENTIALS_KEY, None)
    return render(request, "accounts/account_list.html", {
        "page_title": "Accounts", "rows": rows, "page_obj": page_obj, "counts": counts,
        "role_filter": role_filter, "query": query, "credentials": credentials,
    })


def _create_account(form):
    """Create the user, role group, profile, and linked record as one unit."""
    data = form.cleaned_data
    user = User.objects.create_user(
        username=data["username"], password=data["password"],
        first_name=data["first_name"], last_name=data["last_name"], email=data["email"],
    )
    group_name = ROLE_GROUPS.get(data["role"])
    if group_name:
        user.groups.add(Group.objects.get_or_create(name=group_name)[0])
    user.profile.must_change_password = True
    user.profile.save()
    if data["role"] == "student":
        student = data["student"]
        student.user = user
        student.save()
    if data["role"] == "lecturer":
        Lecturer.objects.create(
            user=user, staff_number=data["staff_number"], title=data["title"],
            department=data["department"], phone=data["phone"] or "",
        )
    return user


@roles_required(ADMIN)
def account_add(request):
    student_preselected = request.GET.get("student")
    initial = {}
    if student_preselected and student_preselected.isdecimal():
        student = Student.objects.filter(user__isnull=True, pk=student_preselected).first()
        if student:
            initial = {"role": "student", "first_name": student.first_name, "last_name": student.last_name,
                       "email": student.email, "student": student.pk}
    form = AccountForm(request.POST or None, creating=True, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = _create_account(form)
        except Exception:
            form.add_error(None, "The account could not be created. Check the details and try again.")
        else:
            request.session[SESSION_CREDENTIALS_KEY] = {"username": user.username, "password": form.cleaned_data["password"]}
            messages.success(request, f"Account created for {user.username}.")
            return redirect("accounts:manage")
    return render(request, "accounts/account_form.html", {
        "page_title": "Add account", "form": form, "creating": True,
    })


def _apply_role_change(user, new_role, cleaned):
    """Move group memberships and linked records so they match the new role."""
    user.groups.remove(*user.groups.filter(name__in=["Admin", "Staff", "Lecturer"]))
    group_name = ROLE_GROUPS.get(new_role)
    if group_name:
        user.groups.add(Group.objects.get_or_create(name=group_name)[0])
    if new_role == "student":
        student = cleaned["student"]
        student.user = user
        student.save()
    elif hasattr(user, "student"):
        # Detach the old student link, keeping the student record itself.
        Student.objects.filter(user=user).update(user=None)
    if new_role == "lecturer":
        lecturer, _ = Lecturer.objects.get_or_create(user=user, defaults={
            "staff_number": cleaned["staff_number"], "title": cleaned["title"],
            "department": cleaned["department"], "phone": cleaned["phone"] or ""})
        lecturer.staff_number = cleaned["staff_number"]
        lecturer.title = cleaned["title"]
        lecturer.department = cleaned["department"]
        lecturer.phone = cleaned["phone"] or ""
        lecturer.save()


@roles_required(ADMIN)
def account_edit(request, pk):
    account = get_object_or_404(User, pk=pk)
    current_role = _role_label(account)
    initial = {
        "first_name": account.first_name, "last_name": account.last_name,
        "email": account.email, "username": account.username, "role": current_role,
        "is_active": account.is_active,
    }
    record = _linked_record(account)
    if record and current_role == "lecturer":
        initial.update({"staff_number": record.staff_number, "title": record.title,
                        "department": record.department_id, "phone": record.phone})
    if record and current_role == "student":
        initial["student"] = record.pk
    form = AccountForm(request.POST or None, initial=initial)
    form.instance_pk = account.pk
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        demoting_self = account == request.user and data["role"] != current_role
        deactivating_self = account == request.user and not data["is_active"]
        losing_admin = current_role == "admin" and (data["role"] != "admin" or not data["is_active"])
        if demoting_self or deactivating_self:
            form.add_error(None, "You cannot change your own role or deactivate yourself.")
        elif losing_admin and not _last_active_admin_exists(account):
            form.add_error(None, "The last active administrator cannot be demoted or deactivated.")
        else:
            with transaction.atomic():
                account.first_name = data["first_name"]
                account.last_name = data["last_name"]
                account.email = data["email"]
                account.username = data["username"]
                account.is_active = data["is_active"]
                account.save()
                if data["role"] != current_role:
                    _apply_role_change(account, data["role"], data)
                elif data["role"] == "lecturer":
                    lecturer = account.lecturer
                    lecturer.staff_number = data["staff_number"]
                    lecturer.title = data["title"]
                    lecturer.department = data["department"]
                    lecturer.phone = data["phone"] or ""
                    lecturer.save()
                AuditLog.objects.create(
                    actor=request.user, action="update", model="User", object_id=account.pk,
                    summary=f"Account updated for {account.username}", snapshot={"role": data["role"]},
                )
            messages.success(request, "Account updated.")
            return redirect("accounts:manage")
    return render(request, "accounts/account_form.html", {
        "page_title": "Edit account", "form": form, "creating": False, "account": account,
        "current_role": current_role,
    })


@roles_required(ADMIN)
def account_reset_password(request, pk):
    """POST only. Generates a temporary password and forces a change at next login."""
    account = get_object_or_404(User, pk=pk)
    if request.method != "POST":
        return redirect("accounts:manage")
    temp = generate_temporary_password()
    account.set_password(temp)
    account.save(update_fields=["password"])
    profile = account.profile
    profile.must_change_password = True
    profile.save()
    AuditLog.objects.create(
        actor=request.user, action="update", model="User", object_id=account.pk,
        summary=f"Password reset for {account.username}", snapshot={},
    )
    request.session[SESSION_CREDENTIALS_KEY] = {"username": account.username, "password": temp}
    messages.success(request, f"Temporary password set for {account.username}.")
    return redirect("accounts:manage")


@roles_required(ADMIN)
def account_toggle(request, pk):
    """POST only. Deactivates or reactivates a login."""
    account = get_object_or_404(User, pk=pk)
    if request.method != "POST":
        return redirect("accounts:manage")
    if account == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("accounts:manage")
    if account.is_active and account.groups.filter(name="Admin").exists() and not _last_active_admin_exists(account):
        messages.error(request, "The last active administrator cannot be deactivated.")
        return redirect("accounts:manage")
    account.is_active = not account.is_active
    account.save(update_fields=["is_active"])
    AuditLog.objects.create(
        actor=request.user, action="update", model="User", object_id=account.pk,
        summary=f"Account {'deactivated' if not account.is_active else 'reactivated'} for {account.username}",
        snapshot={"active": account.is_active},
    )
    messages.success(request, "Account updated.")
    return redirect("accounts:manage")


@roles_required(ADMIN)
def link_students(request):
    """HTMX endpoint for the account form student picker."""
    query = request.GET.get("q", "").strip()
    students = Student.objects.filter(user__isnull=True).select_related("department")
    if query:
        students = students.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(matric_no__icontains=query))
    return render(request, "accounts/_student_options.html", {"students": students[:8], "selected": request.GET.get("selected", "")})
