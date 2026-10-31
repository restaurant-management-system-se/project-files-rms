"""Booking actions reuse the published authentication/resource boundary.

Do not import another app's views (QA-2). Restrict action handlers so the
resource base's generic GET cannot accidentally expose a read endpoint.
"""
from accounts.resources import OwnedResourceView


class BookingActionView(OwnedResourceView):
    http_method_names = ['post', 'options']
