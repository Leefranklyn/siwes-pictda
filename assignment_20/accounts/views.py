from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse

from .forms import RoleAuthenticationForm
from .roles import STUDENT, user_role


class RoleLoginView(LoginView):
    authentication_form = RoleAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse("students:me" if user_role(self.request.user) == STUDENT else "core:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.first_name or self.request.user.username}.")
        return response


class RoleLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been signed out.")
        return response
