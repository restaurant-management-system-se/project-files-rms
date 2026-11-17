from django.contrib.auth import get_user_model
from django.db import connection, transaction

from .models import Booking, BookingOverride, RestaurantTable
from .services import BookingError, create_locked_booking


def locked_staff(user):
    if connection.vendor != 'postgresql':
        raise BookingError('POSTGRESQL_REQUIRED', 'Staff booking actions require PostgreSQL.', 503)
    actor = get_user_model().objects.select_for_update().get(pk=user.pk)
    if not actor.is_active or actor.role not in ['Staff','Admin']:
        raise BookingError('FORBIDDEN', 'Staff or Admin role required.', 403)
    return actor


def staff_create(*, user, customer_id, table_id, start_at, party_size, idempotency_key, reason):
    payload={'customer_id':customer_id,'table_id':table_id,'start_at':start_at.isoformat(),
             'party_size':party_size,'reason':reason}
    with transaction.atomic(durable=True):
        # Staff actor -> customer -> table. Actors cannot be booking customers.
        actor=locked_staff(user)
        previous=BookingOverride.objects.select_related('booking').filter(actor=actor,request_key=idempotency_key).first()
        if previous:
            if previous.payload != payload:
                raise BookingError('IDEMPOTENCY_CONFLICT','Use a new key for a changed request.',409)
            return previous.booking,False
        try:
            customer=get_user_model().objects.select_for_update().get(pk=customer_id,role='Customer',is_active=True)
        except get_user_model().DoesNotExist:
            raise BookingError('CUSTOMER_NOT_FOUND','Choose an active customer account.',404)
        booking=create_locked_booking(customer=customer,table_id=table_id,start_at=start_at,party_size=party_size)
        BookingOverride.objects.create(actor=actor,booking=booking,action='Create',reason=reason,
                                       request_key=idempotency_key,payload=payload)
    return booking,True


def staff_cancel(*, user, booking_id, reason):
    with transaction.atomic(durable=True):
        actor=locked_staff(user)
        record=Booking.objects.filter(pk=booking_id).values('customer_id','table_id').first()
        if record is None:
            raise BookingError('BOOKING_NOT_FOUND','Booking not found.',404)
        get_user_model().objects.select_for_update().get(pk=record['customer_id'])
        RestaurantTable.objects.select_for_update().get(pk=record['table_id'])
        booking=Booking.objects.select_for_update().get(pk=booking_id)
        if booking.status == Booking.Status.CANCELLED:
            return booking,False
        # DEV-02 explicitly permits Staff/Admin cutoff override with a reason.
        booking.status=Booking.Status.CANCELLED
        booking.save(update_fields=['status','updated_at'])
        BookingOverride.objects.create(actor=actor,booking=booking,action='Cancel',reason=reason)
    return booking,True
