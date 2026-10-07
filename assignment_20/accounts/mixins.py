from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .roles import ADMIN, LECTURER, STAFF, user_role


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = ()

    def test_func(self):
        return user_role(self.request.user) in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = (ADMIN,)


class StaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = (ADMIN, STAFF)


class LecturerRequiredMixin(RoleRequiredMixin):
    allowed_roles = (ADMIN, STAFF, LECTURER)


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if user_role(request.user) not in allowed_roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
