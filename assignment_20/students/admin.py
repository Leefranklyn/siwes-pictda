from django.contrib import admin

from .forms import StudentForm
from .models import Course, Department, Enrollment, Guardian, Student


class GuardianInline(admin.TabularInline):
    model = Guardian
    extra = 1


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    form = StudentForm
    list_display = ["matric_no", "first_name", "last_name", "department", "level", "status"]
    search_fields = ["matric_no", "first_name", "last_name", "email"]
    list_filter = ["department", "level", "status"]
    list_select_related = ["department"]
    inlines = [GuardianInline]

    def get_fields(self, request, obj=None):
        return ["user", *StudentForm.Meta.fields]

    def get_exclude(self, request, obj=None):
        from django.conf import settings

        return ["photo"] if not settings.PHOTO_UPLOADS else []


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "session", "semester", "grade"]
    list_filter = ["session", "semester"]
    list_select_related = ["student", "course"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "department", "credit_units"]
    search_fields = ["code", "title"]
    list_select_related = ["department"]


admin.site.register(Department)
admin.site.register(Guardian)
