from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        # Importing connects the audit receivers in core.signals.
        from . import signals  # noqa: F401
