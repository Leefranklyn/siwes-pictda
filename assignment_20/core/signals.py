"""Audit logging: every create, update, or delete of a Student, Course, or
Enrollment writes an AuditLog row. The actor comes from the request user,
captured by core.middleware.AuditUserMiddleware."""
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from students.models import Course, Enrollment, Student

from .middleware import get_current_user
from .models import AuditLog


def snapshot_of(instance):
    """A small JSON record of what the object looked like, for the audit row."""
    if isinstance(instance, Student):
        return {"name": instance.full_name, "matric_no": instance.matric_no}
    if isinstance(instance, Course):
        return {"code": instance.code, "title": instance.title}
    return {
        "matric_no": instance.student.matric_no,
        "course": instance.course.code,
        "session": instance.session,
        "grade": instance.grade,
    }


def audit(instance, action, using, summary=None):
    model_name = type(instance).__name__
    if summary is None:
        if isinstance(instance, Student):
            identity = instance.matric_no
        elif isinstance(instance, Course):
            identity = instance.code
        else:
            identity = f"{instance.student.matric_no}, {instance.course.code}"
        verb = {"create": "created", "update": "updated", "delete": "deleted"}[action]
        summary = f"{model_name} {identity} {verb}"
    AuditLog.objects.using(using).create(
        actor=get_current_user(), action=action, model=model_name,
        object_id=instance.pk, summary=summary[:255], snapshot=snapshot_of(instance),
    )


@receiver(pre_save, sender=Enrollment)
def remember_old_grade(sender, instance, **kwargs):
    # Remember the grade before the save so post_save can tell if it changed.
    if instance.pk:
        old = Enrollment.objects.filter(pk=instance.pk).values_list("grade", flat=True).first()
    else:
        old = None
    instance._old_grade = old


@receiver(post_save, sender=Student)
@receiver(post_save, sender=Course)
@receiver(post_save, sender=Enrollment)
def audit_save(sender, instance, created, raw=False, using="default", **kwargs):
    if raw:
        return
    if created:
        audit(instance, "create", using)
    else:
        old_grade = getattr(instance, "_old_grade", None)
        if sender is Enrollment and old_grade != instance.grade:
            summary = f"Grade for {instance.course.code} set to {instance.grade or 'pending'} ({instance.student.matric_no})"
            if old_grade:
                summary = f"Grade for {instance.course.code} changed from {old_grade} to {instance.grade or 'pending'} ({instance.student.matric_no})"
            audit(instance, "update", using, summary=summary)
        elif sender is not Enrollment or old_grade == instance.grade:
            audit(instance, "update", using)


@receiver(post_delete, sender=Student)
@receiver(post_delete, sender=Course)
@receiver(post_delete, sender=Enrollment)
def audit_delete(sender, instance, using="default", **kwargs):
    audit(instance, "delete", using)
