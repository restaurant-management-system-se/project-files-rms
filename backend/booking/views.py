from accounts.resources import OwnedResourceView
from .models import Booking


class BookingReadView(OwnedResourceView):
    model = Booking
    fields = ("id", "table_id", "start_at", "end_at", "party_size", "status")
