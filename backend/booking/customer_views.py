from collections.abc import Mapping

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrStaffAdmin
from accounts.views import SessionAPIView
from .cancellation import cancel_own_booking
from .models import Booking
from .services import BookingError


class BookingCancelView(SessionAPIView):
    permission_classes = [IsOwnerOrStaffAdmin]

    def post(self, request, pk):
        if request.user.role != 'Customer':
            raise PermissionDenied('Customer self-cancellation is required here.')
        if not isinstance(request.data, Mapping) or request.data:
            return Response({'code': 'INVALID_REQUEST', 'message': 'Send an empty JSON object.'}, status=400)
        try:
            booking, changed = cancel_own_booking(user=request.user, booking_id=pk)
        except BookingError as exc:
            return Response({'code': exc.code, 'message': exc.message}, status=exc.status)
        return Response({'id': booking.pk, 'booking_id': f'BK-{booking.pk}',
                         'status': booking.status, 'changed': changed})


@never_cache
@ensure_csrf_cookie
@require_GET
def my_bookings_page(request):
    if not request.user.is_authenticated:
        return render(request, 'accounts/expired.html', status=401)
    if request.user.role != 'Customer':
        return render(request, 'booking/my_bookings.html', {'forbidden': True}, status=403)
    bookings = Booking.objects.filter(customer=request.user).select_related('table').order_by('-start_at', '-pk')
    page = Paginator(bookings, 25).get_page(request.GET.get('page'))
    return render(request, 'booking/my_bookings.html', {'page': page})
