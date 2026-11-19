from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ImmutableEvents(models.QuerySet):
    def update(self,**kwargs):
        raise PermissionError('Audit events cannot be edited.')

    def delete(self):
        raise PermissionError('Use the trusted retention command for expired events.')


class AuditEvent(models.Model):
    ACTIONS=['MenuCreate','MenuUpdate','MenuDelete','BookingCreate','BookingCancel','OrderStatus']
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    action=models.CharField(max_length=16,choices=[(x,x) for x in ACTIONS])
    object_type=models.CharField(max_length=32)
    object_id=models.PositiveBigIntegerField()
    occurred_at=models.DateTimeField(default=timezone.now,editable=False,db_index=True)
    source_override=models.OneToOneField('booking.BookingOverride',null=True,blank=True,on_delete=models.PROTECT)
    objects=ImmutableEvents.as_manager()

    class Meta:
        constraints=[models.CheckConstraint(condition=Q(action__in=['MenuCreate','MenuUpdate','MenuDelete','BookingCreate','BookingCancel','OrderStatus']),name='audit_valid_action')]
        ordering=['-occurred_at','-pk']

    def save(self,*args,**kwargs):
        if not self._state.adding:
            raise PermissionError('Audit events cannot be edited.')
        return super().save(*args,**kwargs)

    def delete(self,*args,**kwargs):
        raise PermissionError('Audit events cannot be deleted through the application.')
