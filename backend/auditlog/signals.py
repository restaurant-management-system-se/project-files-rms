from django.core.exceptions import PermissionDenied
from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver

from booking.models import BookingOverride
from menu.models import MenuItem
from orders.models import Order
from .services import current_actor, record_event, record_override


@receiver(post_save,sender=BookingOverride,dispatch_uid='audit_booking_override')
def booking_override(sender,instance,created,raw=False,**kwargs):
    if created and not raw: record_override(instance)


@receiver(pre_save,sender=MenuItem,dispatch_uid='audit_menu_before')
def menu_before(sender,instance,raw=False,**kwargs):
    actor=current_actor.get()
    if raw or actor is None: return
    if actor.role!='Admin': raise PermissionDenied('Menu changes require Admin.')
    instance._audit_before=sender.objects.filter(pk=instance.pk).values('name','category','price','available').first()


@receiver(post_save,sender=MenuItem,dispatch_uid='audit_menu_after')
def menu_after(sender,instance,created,raw=False,**kwargs):
    actor=current_actor.get()
    if raw or actor is None: return
    before=getattr(instance,'_audit_before',None)
    after=sender.objects.filter(pk=instance.pk).values('name','category','price','available').get()
    if created or before!=after:
        record_event(actor=actor,action='MenuCreate' if created else 'MenuUpdate',object_type='menu.MenuItem',object_id=instance.pk)


@receiver(pre_delete,sender=MenuItem,dispatch_uid='audit_menu_delete')
def menu_delete(sender,instance,**kwargs):
    actor=current_actor.get()
    if actor is not None:
        record_event(actor=actor,action='MenuDelete',object_type='menu.MenuItem',object_id=instance.pk)


@receiver(pre_save,sender=Order,dispatch_uid='audit_order_before')
def order_before(sender,instance,raw=False,**kwargs):
    if not raw and current_actor.get() is not None:
        instance._audit_status=sender.objects.filter(pk=instance.pk).values_list('status',flat=True).first()


@receiver(post_save,sender=Order,dispatch_uid='audit_order_after')
def order_after(sender,instance,created,raw=False,**kwargs):
    actor=current_actor.get()
    if raw or actor is None or created: return
    # Compare persisted state: update_fields may intentionally omit status.
    status=sender.objects.values_list('status',flat=True).get(pk=instance.pk)
    if getattr(instance,'_audit_status',status)!=status:
        record_event(actor=actor,action='OrderStatus',object_type='orders.Order',object_id=instance.pk)
