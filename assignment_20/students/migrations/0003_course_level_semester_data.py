from django.db import migrations


def set_level_and_semester_from_code(apps, schema_editor):
    """CSC201 becomes 200 level, ITE301 becomes 300 level; odd last digit is
    first semester, even is second."""
    course = apps.get_model("students", "Course")
    for row in course.objects.all():
        digits = "".join(char for char in row.code if char.isdigit())
        if len(digits) >= 3:
            row.level = int(digits[-3]) * 100
        row.semester = "second" if digits and int(digits[-1]) % 2 == 0 else "first"
        row.save(update_fields=["level", "semester"])


class Migration(migrations.Migration):
    dependencies = [("students", "0002_course_level_course_semester_enrollment_graded_at_and_more")]
    operations = [migrations.RunPython(set_level_and_semester_from_code, migrations.RunPython.noop)]
