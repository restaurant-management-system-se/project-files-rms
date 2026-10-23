from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone

from .availability import duration
from .models import Booking, BookingRequestKey, RestaurantTable


class BookingError(Exception):
    def __init__(self, code, message, status, details=None):
        self.code, self.message, self.status = code, message, status
        self.details = details or {}
        super().__init__(message)


def confirm_booking(*, user, table_id, start_at, party_size, idempotency_key):
    if connection.vendor != 'postgresql':
        raise BookingError('POSTGRESQL_REQUIRED', 'Booking confirmation requires PostgreSQL.', 503)
    payload = {'table_id': table_id, 'start_at': start_at.isoformat(), 'party_size': party_size}
    # Lock order is always customer, then table. The customer lock serializes
    # same-customer retries, even when the same key names different tables.
    # durable=True ensures confirmation cannot escape an uncommitted outer tx.
    with transaction.atomic(durable=True):
        actor = get_user_model().objects.select_for_update().get(pk=user.pk)
        if not actor.is_active or actor.role != 'Customer':
            raise BookingError('FORBIDDEN', 'Customer self-booking is required here.', 403)
        previous = BookingRequestKey.objects.select_related('booking').filter(
            customer=actor, key=idempotency_key).first()
        if previous:
            if previous.payload != payload:
                raise BookingError('IDEMPOTENCY_CONFLICT', 'Use a new key for a changed booking request.', 409)
            return previous.booking, False
        if start_at <= timezone.now():
            raise BookingError('INVALID_REQUEST', 'Choose a future date and time.', 400,
                               {'start_at': ['Choose a future date and time.']})
        try:
            table = RestaurantTable.objects.select_for_update().get(pk=table_id)
        except RestaurantTable.DoesNotExist:
            raise BookingError('TABLE_NOT_FOUND', 'The selected table does not exist.', 404)
        if not table.active or table.capacity < party_size:
            raise BookingError('TABLE_UNAVAILABLE', 'The selected table cannot seat this party.', 409)
        end_at = start_at + duration()
        if Booking.objects.filter(table=table, status=Booking.Status.CONFIRMED,
                                  start_at__lt=end_at, end_at__gt=start_at).exists():
            raise BookingError('TABLE_UNAVAILABLE', 'The selected table is no longer available.', 409)
        booking = Booking.objects.create(customer=actor, table=table, start_at=start_at,
                                        end_at=end_at, party_size=party_size)
        BookingRequestKey.objects.create(customer=actor, key=idempotency_key,
                                         payload=payload, booking=booking)
    return booking, True
