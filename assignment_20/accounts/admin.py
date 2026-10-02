from django.contrib.admin import AdminSite
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .roles import ADMIN, user_role


class RoleAdminSite(AdminSite):
    site_header = "Student Records administration"
    site_title = "Student Records"

    def has_permission(self, request):
        if request.user.is_authenticated and user_role(request.user) != ADMIN:
            raise PermissionDenied
        return request.user.is_active and user_role(request.user) == ADMIN

    def login(self, request, extra_context=None):
        if request.user.is_authenticated:
            if user_role(request.user) != ADMIN:
                raise PermissionDenied
            return redirect("admin:index")
        from django.contrib.auth.views import redirect_to_login

        return redirect_to_login(request.GET.get("next", "/admin/"))
