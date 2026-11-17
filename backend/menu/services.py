"""Menu-owned mutations. The shared audit adapter is used when RMS-23 is installed."""
from contextlib import contextmanager
from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from .models import MenuItem

@contextmanager
def privileged_change(user, *, menu=False):
    if apps.is_installed('auditlog'):
        from auditlog.services import audited_change
        with audited_change(user) as actor:
            # audited_change validates Staff/Admin; menu remains Admin only.
            if menu and get_user_model().objects.get(pk=user.pk).role != 'Admin':
                raise PermissionDenied('Admin role required.')
            yield actor
    else:
        with transaction.atomic():
            actor = get_user_model().objects.select_for_update().get(pk=user.pk)
            if not actor.is_active or actor.role not in (('Admin',) if menu else ('Admin', 'Staff')):
                raise PermissionDenied('Permission denied.')
            yield actor

def save_menu(user, serializer, pk=None):
    with privileged_change(user, menu=True):
        if pk is not None:
            serializer.instance = MenuItem.objects.select_for_update().get(pk=pk)
        before = None
        if serializer.instance is not None:
            before = {k: getattr(serializer.instance, k) for k in ('name','category','price','available','description')}
        item = serializer.save()
        # RMS-23's original signal watches the pre-existing fields. Capture a
        # description-only edit without duplicating events for other changes.
        if apps.is_installed('auditlog') and before and before['description'] != item.description and all(before[k] == getattr(item,k) for k in ('name','category','price','available')):
            from auditlog.services import record_event
            record_event(actor=get_user_model().objects.get(pk=user.pk), action='MenuUpdate', object_type='menu.MenuItem', object_id=item.pk)
        return item

def delete_menu(user, pk):
    with privileged_change(user, menu=True):
        item = MenuItem.objects.select_for_update().get(pk=pk)
        # Order rows keep their PROTECT reference; never erase historical items.
        if item.order_items.exists():
            item.available = False
            item.save(update_fields=['available'])
            return False
        item.delete()
        return True
