"""RMS-10 customer cancellation. Shared entity fields and auth stay unchanged."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone

from .models import Booking, RestaurantTable
from .services import BookingError


def cancel_own_booking(*, user, booking_id):
    if connection.vendor != 'postgresql':
        raise BookingError('POSTGRESQL_REQUIRED', 'Booking cancellation requires PostgreSQL.', 503)
    # Match confirmation's customer -> table lock order. Never lock a booking
    # before its table; future staff operations must use this same protocol.
    with transaction.atomic(durable=True):
        actor = get_user_model().objects.select_for_update().get(pk=user.pk)
        if not actor.is_active or actor.role != 'Customer':
            raise BookingError('FORBIDDEN', 'Customer self-cancellation is required here.', 403)
        record = Booking.objects.filter(pk=booking_id, customer=actor).values('table_id').first()
        if record is None:
            raise BookingError('BOOKING_NOT_FOUND', 'Booking not found.', 404)
        RestaurantTable.objects.select_for_update().get(pk=record['table_id'])
        booking = Booking.objects.select_for_update().get(pk=booking_id, customer=actor)
        # A retry remains successful after the cutoff if already cancelled.
        if booking.status == Booking.Status.CANCELLED:
            return booking, False
        if booking.start_at - timezone.now() < timedelta(minutes=30):
            raise BookingError('CANCELLATION_CUTOFF', 'Cancel at least 30 minutes before the booking starts.', 409)
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=['status', 'updated_at'])
    return booking, True
