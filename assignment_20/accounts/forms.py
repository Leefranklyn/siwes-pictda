import secrets

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from students.forms import TailwindFormMixin
from students.models import Department, Lecturer, Student

ROLE_CHOICES = [
    ("admin", "Admin"), ("staff", "Staff"), ("lecturer", "Lecturer"), ("student", "Student"),
]


def generate_temporary_password(length=12):
    alphabet = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class RoleAuthenticationForm(TailwindFormMixin, AuthenticationForm):
    error_messages = {
        "invalid_login": "That username and password do not match. Check both and try again.",
        "inactive": "That username and password do not match. Check both and try again.",
    }


class StyledPasswordChangeForm(TailwindFormMixin, PasswordChangeForm):
    pass


class StyledPasswordResetForm(TailwindFormMixin, PasswordResetForm):
    pass


class AccountForm(TailwindFormMixin, forms.Form):
    """Create or edit a login and its role. One form serves both add and edit;
    on edit the password and linked-record fields are hidden or optional."""

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    username = forms.RegexField(r"^[\w.@+-]+$", max_length=150)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    password = forms.CharField(
        label="Temporary password", max_length=128, required=False,
        help_text="They must choose a new password at first sign in.",
    )
    student = forms.ModelChoiceField(queryset=Student.objects.none(), required=False)
    staff_number = forms.CharField(max_length=30, required=False)
    title = forms.ChoiceField(choices=[("", "-")] + list(Lecturer.TITLES), required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)
    phone = forms.CharField(max_length=20, required=False)
    is_active = forms.BooleanField(label="Active", required=False, initial=True)

    def __init__(self, *args, creating=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.creating = creating
        self.instance_pk = None
        # Only students without a login can be linked to a new account.
        self.fields["student"].queryset = Student.objects.filter(user__isnull=True)
        if not creating:
            self.fields["password"].required = False

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        existing = User.objects.filter(username__iexact=username)
        if self.instance_pk:
            existing = existing.exclude(pk=self.instance_pk)
        if existing.exists():
            raise ValidationError("A user with that username already exists.")
        return username

    def clean_staff_number(self):
        value = self.cleaned_data.get("staff_number", "").strip().upper()
        if value:
            duplicate = Lecturer.objects.filter(staff_number__iexact=value)
            if self.instance_pk:
                duplicate = duplicate.exclude(user_id=self.instance_pk)
            if duplicate.exists():
                raise ValidationError("A lecturer with this staff number already exists.")
        return value

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        if self.creating and not cleaned.get("password"):
            self.add_error("password", "Set a temporary password, or press Generate.")
        if role == "student" and not cleaned.get("student"):
            self.add_error("student", "Choose the student this login belongs to.")
        if role == "lecturer":
            for field in ("staff_number", "title", "department"):
                if not cleaned.get(field):
                    self.add_error(field, "This field is required for a lecturer.")
        return cleaned
