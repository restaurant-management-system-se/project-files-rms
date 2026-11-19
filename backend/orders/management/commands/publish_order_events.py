from django.core.management.base import BaseCommand
from orders.models import OrderEvent
from orders.events import dispatch_event
class Command(BaseCommand):
    help='Retry up to 100 committed order events. Run periodically under the trusted operator.'
    def handle(self,*args,**kwargs):
        count=0
        for event_id in OrderEvent.objects.filter(delivered_at__isnull=True).order_by('timestamp').values_list('pk',flat=True)[:100]:
            count+=int(dispatch_event(event_id))
        self.stdout.write(f'Delivered {count} pending order events.')
