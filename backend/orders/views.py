from accounts.resources import OwnedResourceView
from .models import Order


class OrderReadView(OwnedResourceView):
    model = Order
    fields = ("id", "booking_id", "status", "total_amount", "placed_at")
