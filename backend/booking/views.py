from accounts.resources import OwnedResourceView
from .models import Booking


class BookingReadView(OwnedResourceView):
    model = Booking
    fields = ("id", "table_id", "start_at", "end_at", "party_size", "status")


from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .availability import availability
from .serializers import AvailabilityQuery


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def table_availability(request):
    query = AvailabilityQuery(data=request.query_params)
    if not query.is_valid():
        return Response({"code": "INVALID_REQUEST", "message": "Check the highlighted fields.",
                         "details": query.errors}, status=400)
    return Response(availability(**query.validated_data))


@ensure_csrf_cookie
def booking_page(request):
    return render(request, "booking/book.html")
