from django.conf import settings
from django.db import models
from django.db.models import F, Q


class RestaurantTable(models.Model):
    table_number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(capacity__gt=0), name="table_positive_capacity")]

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} seats)"


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "Confirmed"
        CANCELLED = "Cancelled"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    table = models.ForeignKey(RestaurantTable, on_delete=models.PROTECT, related_name="bookings")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    party_size = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=10, choices=Status, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(start_at__lt=F("end_at")), name="booking_valid_interval"),
            models.CheckConstraint(condition=Q(party_size__gt=0), name="booking_positive_party"),
            models.CheckConstraint(condition=Q(status__in=["Confirmed", "Cancelled"]), name="booking_valid_status"),
        ]
        indexes = [models.Index(fields=["table", "status", "start_at"], name="booking_availability_idx")]


# Register the booking-owned idempotency model without altering shared entities.
from .request_models import BookingRequestKey  # noqa: E402,F401
from .staff_models import BookingOverride  # noqa: E402,F401
