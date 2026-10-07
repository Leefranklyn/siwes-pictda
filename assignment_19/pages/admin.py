from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin configuration for the Student model."""

    list_display = ('name', 'age', 'course', 'phone', 'email', 'registered_at')
    search_fields = ('name', 'email', 'course')
