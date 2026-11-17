"""Booking-only override evidence; no general security audit service."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class BookingOverride(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='booking_overrides')
    booking = models.ForeignKey('booking.Booking', on_delete=models.PROTECT, related_name='overrides')
    action = models.CharField(max_length=6, choices=[('Create','Create'),('Cancel','Cancel')])
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    request_key = models.CharField(max_length=128, null=True)
    payload = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['actor','request_key'], name='booking_override_actor_key'),
            models.CheckConstraint(condition=Q(action__in=['Create','Cancel']), name='booking_override_action'),
            models.CheckConstraint(condition=~Q(reason=''), name='booking_override_reason'),
        ]
