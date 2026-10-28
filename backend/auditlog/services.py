from contextlib import contextmanager
from contextvars import ContextVar
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import connection, models, transaction
from django.utils import timezone

from .models import AuditEvent

current_actor=ContextVar('rms_audit_actor',default=None)


@contextmanager
def audited_change(user):
    """Feature-owner adapter: wrap an authorized menu/order mutation atomically."""
    with transaction.atomic():
        actor=get_user_model().objects.select_for_update().get(pk=user.pk)
        if not actor.is_active or actor.role not in ['Staff','Admin']:
            raise PermissionDenied('Privileged audit actor required.')
        token=current_actor.set(actor)
        try:
            yield
        finally:
            current_actor.reset(token)


def record_event(*, actor, action, object_type, object_id):
    if not connection.in_atomic_block:
        raise RuntimeError('Business mutation and audit must share a transaction.')
    allowed={'MenuCreate':'menu.MenuItem','MenuUpdate':'menu.MenuItem','MenuDelete':'menu.MenuItem',
             'OrderStatus':'orders.Order'}
    if allowed.get(action)!=object_type:
        raise ValueError('Unsupported audit action/target.')
    if not actor.is_active or actor.role not in (['Admin'] if action.startswith('Menu') else ['Staff','Admin']):
        raise PermissionDenied('Actor cannot perform this action.')
    return AuditEvent.objects.create(actor=actor,action=action,object_type=object_type,object_id=object_id)


def record_override(override):
    if not connection.in_atomic_block:
        raise RuntimeError('Booking override and audit must share a transaction.')
    # Derive only from persisted booking-owned evidence, including its original
    # actor/time during backfill. Never copy free-text reasons or retry payloads.
    event,_=AuditEvent.objects.get_or_create(source_override=override,defaults={
        'actor_id':override.actor_id,'action':'Booking'+override.action,
        'object_type':'booking.Booking','object_id':override.booking_id,
        'occurred_at':override.created_at})
    return event


def purge_expired(*, now=None):
    """Trusted operator only. Strictly older than 90 days, preserving boundary."""
    threshold=(now or timezone.now())-timedelta(days=90)
    # Deliberately bypass the application's immutable QuerySet only here.
    expired=models.QuerySet(model=AuditEvent,using='default').filter(occurred_at__lt=threshold)
    return expired.delete()[0]
