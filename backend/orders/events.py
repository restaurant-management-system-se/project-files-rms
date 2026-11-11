"""Persist before commit; deliver after commit with retryable outbox semantics."""
import json
import logging
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.parse import urlparse
from urllib.error import URLError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import OrderEvent
logger=logging.getLogger(__name__)
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def event_payload(event):
    return {'event_id':str(event.pk),'order_id':event.order_id,'status':event.status,'version':event.version,'timestamp':event.timestamp.isoformat()}
def queue_event(order):
    event=OrderEvent.objects.create(order=order,version=order.version,status=order.status)
    transaction.on_commit(lambda:dispatch_event(event.pk))
    return event

def dispatch_event(event_id):
    event=OrderEvent.objects.get(pk=event_id)
    if event.delivered_at:return True
    endpoint=getattr(settings,'RMS_REALTIME_INTERNAL_URL','')
    key=getattr(settings,'RMS_REALTIME_KEY','')
    if not endpoint or len(key)<32:return False
    target=urlparse(endpoint)
    if target.username or target.password or target.scheme not in ['http','https'] or (target.scheme!='https' and target.hostname not in ['127.0.0.1','localhost','::1']):return False
    try:
        request=Request(endpoint.rstrip('/')+'/internal/events',data=json.dumps({'event_id':str(event.pk)}).encode(),headers={'Content-Type':'application/json','X-RMS-Key':key},method='POST')
        with build_opener(NoRedirect()).open(request,timeout=3) as response:
            if response.status!=200:return False
    except (URLError,TimeoutError,OSError):
        logger.warning('Order event remains pending for retry')
        return False
    OrderEvent.objects.filter(pk=event.pk,delivered_at__isnull=True).update(delivered_at=timezone.now())
    return True
