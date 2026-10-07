"""
This app defines a Student model used by the registration page.
"""

from django.db import models


class Student(models.Model):
    """A student registered through the website."""

    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    course = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.course})"
