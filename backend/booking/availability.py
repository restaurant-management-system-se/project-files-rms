"""Read-only interval availability. Booking creation must recheck under a row lock."""
from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Booking, RestaurantTable


def duration():
    return timedelta(minutes=getattr(settings, "BOOKING_DURATION_MINUTES", 90))


def table_data(table):
    return {"table_id": table.pk, "table_number": table.table_number, "capacity": table.capacity}


def availability(start_at, party_size, *, now=None):
    now = now or timezone.now()
    length = duration()
    tables = list(RestaurantTable.objects.filter(active=True, capacity__gte=party_size)
                  .order_by("capacity", "table_number"))
    intervals = defaultdict(list)
    for table_id, start, end in Booking.objects.filter(
        table_id__in=[t.pk for t in tables], status=Booking.Status.CONFIRMED,
        end_at__gt=now,
    ).order_by("start_at", "end_at").values_list("table_id", "start_at", "end_at"):
        intervals[table_id].append((start, end))

    free, candidates = [], []
    for table in tables:
        busy = intervals[table.pk]
        if not any(a < start_at + length and b > start_at for a, b in busy):
            free.append(table_data(table))
        # Union busy intervals, then clamp requested start into each free gap.
        # This finds the nearest exact interval, without sampling or a finite horizon.
        cursor = now + timedelta(microseconds=1)
        for a, b in busy:
            if a - cursor >= length:
                candidate = min(max(start_at, cursor), a - length)
                candidates.append((candidate, table))
            cursor = max(cursor, b)
        candidates.append((max(cursor, start_at), table))

    candidates.sort(key=lambda item: (abs(item[0] - start_at), item[0],
                                     item[1].capacity, item[1].table_number))
    nearest = None
    if not free and candidates:
        candidate, table = candidates[0]
        nearest = {**table_data(table), "start_at": candidate, "end_at": candidate + length}
    return {"start_at": start_at, "end_at": start_at + length,
            "party_size": party_size, "tables": free, "alternative": nearest}
