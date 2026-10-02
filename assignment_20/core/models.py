from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTIONS = [("create", "Created"), ("update", "Updated"), ("delete", "Deleted")]
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=6, choices=ACTIONS)
    model = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    summary = models.CharField(max_length=255)
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.summary
