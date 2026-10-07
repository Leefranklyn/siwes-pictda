from django.core.management.base import BaseCommand

from core.models import ImportBatch
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Remove uploaded rows from stale previewed import batches older than 24 hours."

    def handle(self, *args, **options):
        stale = ImportBatch.objects.filter(status="previewed", created_at__lt=timezone.now() - timedelta(hours=24))
        count = stale.update(rows=[])
        self.stdout.write(f"Cleared rows from {count} stale import batches.")
