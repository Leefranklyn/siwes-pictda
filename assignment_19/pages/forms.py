"""
Forms used by the contact and register pages.
"""

from django import forms

from .models import Student


class ContactForm(forms.Form):
    """A simple contact form shown on the contact page."""

    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))


class RegisterForm(forms.ModelForm):
    """A form for registering a student through the website."""

    class Meta:
        model = Student
        fields = ['name', 'age', 'course', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full name'}),
            'age': forms.NumberInput(attrs={'min': 1, 'max': 120}),
            'phone': forms.TextInput(attrs={'placeholder': 'e.g. 08012345678'}),
        }
