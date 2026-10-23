"""Booking-owned retry metadata; RMS-03 shared entity fields remain unchanged."""
from django.conf import settings
from django.db import models

from .models import Booking


class BookingRequestKey(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.CharField(max_length=128)
    payload = models.JSONField()
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["customer", "key"], name="booking_customer_request_key")]
