from accounts.resources import OwnedResourceView
from .models import Booking


class BookingReadView(OwnedResourceView):
    model = Booking
    fields = ("id", "table_id", "start_at", "end_at", "party_size", "status")


from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
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


@never_cache
@ensure_csrf_cookie
def booking_page(request):
    return render(request, "booking/book.html")


# Reuse Noctowl's shared session/ownership boundary through BookingReadView.
# GET keeps its original ownership filtering; POST adds only this issue's
# Customer self-booking behavior. Staff on-behalf work remains RMS-11.
from rest_framework.exceptions import PermissionDenied
from .serializers import BookingCreate
from .services import BookingError, confirm_booking


class BookingView(BookingReadView):
    def post(self, request):
        if request.user.role != 'Customer':
            raise PermissionDenied('Customer self-booking is required here.')
        data = BookingCreate(data=request.data)
        if not data.is_valid():
            return Response({'code': 'INVALID_REQUEST', 'message': 'Check the highlighted fields.',
                             'details': data.errors}, status=400)
        try:
            booking, created = confirm_booking(user=request.user, **data.validated_data)
        except BookingError as exc:
            details = exc.details
            if exc.code == 'TABLE_UNAVAILABLE':
                options = availability(data.validated_data['start_at'], data.validated_data['party_size'])
                details = {**options, 'suggested_start_at': (options['alternative'] or {}).get('start_at')}
            return Response({'code': exc.code, 'message': exc.message, 'details': details}, status=exc.status)
        return Response({'booking_id': f'BK-{booking.pk}', 'status': booking.status,
                         'customer_id': booking.customer_id, 'table_id': booking.table_id,
                         'start_at': booking.start_at, 'end_at': booking.end_at,
                         'party_size': booking.party_size}, status=201 if created else 200)
