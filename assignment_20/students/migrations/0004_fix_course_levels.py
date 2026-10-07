from django.db import migrations


def fix_levels(apps, schema_editor):
    """Correct levels set by an earlier buggy pass (CSC201 became 2 instead of 200)."""
    course = apps.get_model("students", "Course")
    for row in course.objects.all():
        digits = "".join(char for char in row.code if char.isdigit())
        if len(digits) >= 3:
            row.level = int(digits[-3]) * 100
            row.save(update_fields=["level"])


class Migration(migrations.Migration):
    dependencies = [("students", "0003_course_level_semester_data")]
    operations = [migrations.RunPython(fix_levels, migrations.RunPython.noop)]
