from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTIONS = [
        ("create", "Created"), ("update", "Updated"), ("delete", "Deleted"),
        ("import", "Imported"), ("export", "Exported"),
    ]
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=7, choices=ACTIONS)
    model = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    summary = models.CharField(max_length=255)
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.summary


class ImportBatch(models.Model):
    KINDS = [("students", "Students"), ("grades", "Grades"), ("courses", "Courses")]
    STATUSES = [("previewed", "Previewed"), ("confirmed", "Confirmed"), ("discarded", "Discarded")]

    kind = models.CharField(max_length=10, choices=KINDS)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="import_batches")
    filename = models.CharField(max_length=255)
    # Validated rows waiting for confirmation; cleared once the import is confirmed.
    rows = models.JSONField(default=list, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    errors = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="previewed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} import of {self.filename} ({self.status})"
