from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy

from .forms import RoleAuthenticationForm, StyledPasswordChangeForm, StyledPasswordResetForm
from .roles import ADMIN, LECTURER, STAFF, STUDENT, user_role

# Where each role lands after signing in.
HOME_URLS = {ADMIN: "core:dashboard", STAFF: "core:dashboard", LECTURER: "students:teaching", STUDENT: "students:me"}


class RoleLoginView(auth_views.LoginView):
    authentication_form = RoleAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.get_redirect_url():
            return self.get_redirect_url()
        return reverse(HOME_URLS.get(user_role(self.request.user), "core:dashboard"))

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.first_name or self.request.user.username}.")
        return response


class RoleLogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been signed out.")
        return response


class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    form_class = StyledPasswordChangeForm
    template_name = "registration/password_change.html"

    def get_success_url(self):
        return reverse(HOME_URLS.get(user_role(self.request.user), "core:dashboard"))

    def form_valid(self, form):
        response = super().form_valid(form)
        profile = self.request.user.profile
        profile.must_change_password = False
        profile.save()
        messages.success(self.request, "Password updated.")
        return response


class PasswordResetView(auth_views.PasswordResetView):
    form_class = StyledPasswordResetForm
    template_name = "registration/password_reset.html"
    email_template_name = "registration/password_reset_email.txt"
    success_url = reverse_lazy("accounts:login")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:login")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"
