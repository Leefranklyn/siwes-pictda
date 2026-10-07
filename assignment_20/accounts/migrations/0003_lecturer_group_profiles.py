from django.db import migrations


def create_group_and_profiles(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    profile = apps.get_model("accounts", "UserProfile")
    group.objects.using(schema_editor.connection.alias).get_or_create(name="Lecturer")
    for user in apps.get_model("auth", "User").objects.all():
        profile.objects.using(schema_editor.connection.alias).get_or_create(user=user)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_initial")]
    operations = [migrations.RunPython(create_group_and_profiles, migrations.RunPython.noop)]
