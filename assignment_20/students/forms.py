from django import forms
from django.conf import settings
from django.forms import inlineformset_factory

from .models import Course, Department, Enrollment, Guardian, Student


INPUT = ("block w-full border border-line-strong bg-bg px-3.5 py-2.5 text-sm text-fg "
         "placeholder:text-faint focus:border-accent-ink focus:outline-none "
         "aria-[invalid=true]:border-danger")
CHECK = "h-4 w-4 accent-accent-ink"
FILE = ("block w-full text-sm text-mute file:mr-4 file:border-0 file:bg-surface-2 "
        "file:px-4 file:py-2 file:text-sm file:font-medium file:text-fg hover:file:bg-line")


class TailwindFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                # Option lists render their inputs inside labelled rows; the
                # component CSS sizes them, so they must not inherit the
                # full-width text-input classes.
                continue
            if isinstance(widget, forms.CheckboxInput):
                css = CHECK
            elif isinstance(widget, forms.FileInput):
                css = FILE
            else:
                css = INPUT
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class StudentForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Student
        fields = ["first_name", "last_name", "dob", "gender", "photo", "email", "phone", "address",
                  "matric_no", "department", "level", "status", "enrolled_on"]
        labels = {"matric_no": "Matric number", "enrolled_on": "Enrolled on"}
        help_texts = {"matric_no": "Format: VUG/CSC/24/10001"}
        widgets = {
            "dob": forms.DateInput(attrs={"type": "date"}),
            "enrolled_on": forms.DateInput(attrs={"type": "date"}),
            "matric_no": forms.TextInput(attrs={"class": "font-mono"}),
            "address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.PHOTO_UPLOADS:
            self.fields.pop("photo")

    def clean_matric_no(self):
        value = self.cleaned_data["matric_no"].strip().upper()
        if Student.objects.filter(matric_no__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A student with this matric number already exists.")
        return value

    def clean_email(self):
        value = self.cleaned_data["email"].strip().lower()
        if Student.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A student with this email already exists.")
        return value


class GuardianForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ["full_name", "relationship", "phone", "email"]


GuardianFormSet = inlineformset_factory(Student, Guardian, form=GuardianForm, extra=1, can_delete=True)


class CourseForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ["code", "title", "credit_units", "department", "level", "semester", "lecturers"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "font-mono"}),
            "lecturers": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lecturers"].help_text = "Lecturers from other departments are allowed."
        self.fields["lecturers"].label_from_instance = lambda lecturer: (
            f"{lecturer.full_name}, {lecturer.department.name} ({lecturer.staff_number})")

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        duplicate = Course.objects.filter(code__iexact=code)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("A course with this code already exists.")
        return code


class DepartmentForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        duplicate = Department.objects.filter(name__iexact=name)
        if self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("A department with this name already exists.")
        return name


class StudentImportForm(forms.Form):
    """Upload step for the students CSV import."""
    file = forms.FileField(label="CSV file")
    skip_errors = forms.BooleanField(label="Skip rows with errors", required=False, initial=False)
    create_logins = forms.BooleanField(label="Create a login for each new student", required=False, initial=False)


class EnrollmentForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["course", "session", "semester", "grade"]
        widgets = {"session": forms.TextInput(attrs={"placeholder": "2025/2026"})}

    def __init__(self, *args, student, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.student = student

    def clean(self):
        data = super().clean()
        if data.get("course") and data.get("session"):
            duplicate = Enrollment.objects.filter(student=self.instance.student, course=data["course"], session=data["session"])
            if duplicate.exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("This student is already enrolled in that course for this session.")
        return data
