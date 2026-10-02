from django.contrib.auth.forms import AuthenticationForm

from students.forms import TailwindFormMixin


class RoleAuthenticationForm(TailwindFormMixin, AuthenticationForm):
    error_messages = {
        "invalid_login": "That username and password do not match. Check both and try again.",
        "inactive": "That username and password do not match. Check both and try again.",
    }
