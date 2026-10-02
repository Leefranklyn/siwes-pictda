from django.db.models.signals import post_delete, post_save

from students.models import Course, Enrollment, Student
from .middleware import get_current_user
from .models import AuditLog


def record_audit(sender, instance, action, using):
    if isinstance(instance, Student):
        identity = instance.matric_no
        snapshot = {"name": instance.full_name, "matric_no": instance.matric_no}
    elif isinstance(instance, Course):
        identity = instance.code
        snapshot = {"code": instance.code, "title": instance.title}
    else:
        identity = f"{instance.student.matric_no}, {instance.course.code}"
        snapshot = {"matric_no": instance.student.matric_no, "course": instance.course.code, "session": instance.session, "grade": instance.grade}
    verb = {"create": "created", "update": "updated", "delete": "deleted"}[action]
    AuditLog.objects.using(using).create(
        actor=get_current_user(), action=action, model=sender.__name__, object_id=instance.pk,
        summary=f"{sender.__name__} {identity} {verb}"[:255], snapshot=snapshot,
    )


def audit_save(sender, instance, created, raw=False, using="default", **kwargs):
    if not raw:
        record_audit(sender, instance, "create" if created else "update", using)


def audit_delete(sender, instance, using="default", **kwargs):
    record_audit(sender, instance, "delete", using)


def connect_audit_signals():
    for model in (Student, Enrollment, Course):
        post_save.connect(audit_save, sender=model, dispatch_uid=f"audit_save_{model.__name__}")
        post_delete.connect(audit_delete, sender=model, dispatch_uid=f"audit_delete_{model.__name__}")
