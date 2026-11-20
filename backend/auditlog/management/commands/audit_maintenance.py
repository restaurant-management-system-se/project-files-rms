from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from booking.models import BookingOverride
from auditlog.models import AuditEvent
from auditlog.services import purge_expired, record_override


class Command(BaseCommand):
    help='Trusted operator audit backfill/retention. Dry run unless --execute.'

    def add_arguments(self,parser):
        parser.add_argument('--execute',action='store_true')
        parser.add_argument('--backfill',action='store_true')

    def handle(self,*args,**options):
        now=timezone.now()
        expired=AuditEvent.objects.filter(occurred_at__lt=now-timedelta(days=90)).count()
        missing=BookingOverride.objects.filter(auditevent__isnull=True)
        self.stdout.write(f'Expired events: {expired}; booking overrides missing events: {missing.count()}')
        if options['execute']:
            with transaction.atomic():
                if options['backfill']:
                    for override in missing.iterator(): record_override(override)
                deleted=purge_expired(now=now)
            self.stdout.write(f'Deleted expired events: {deleted}')
        else:
            self.stdout.write('Dry run; no data changed.')
