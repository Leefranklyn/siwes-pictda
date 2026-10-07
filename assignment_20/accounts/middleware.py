from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


class MustChangePasswordMiddleware:
    """Users with must_change_password=True may only visit the password change
    and logout pages until they choose a new password."""

    ALLOWED_PREFIXES = ("/accounts/password/change/", "/accounts/logout/", "/static/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and getattr(user, "profile", None) and user.profile.must_change_password:
            if not any(request.path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
                messages.warning(request, "Choose a new password to continue.")
                return redirect("accounts:password_change")
        return self.get_response(request)
