from django.urls import path
from . import views
from .customer_views import BookingCancelView, my_bookings_page
from .staff_views import StaffBookingsView, StaffCancelView, StaffBookingPage

urlpatterns = [
    path('staff/bookings/', StaffBookingPage.as_view(), name='staff-bookings'),
    path('api/staff/bookings', StaffBookingsView.as_view(), name='staff-bookings-api'),
    path('api/staff/bookings/<int:pk>/cancel', StaffCancelView.as_view(), name='staff-booking-cancel'),
    path("api/tables/availability", views.table_availability, name="table-availability"),
    path("book/", views.booking_page, name="booking-page"),
    path("my-bookings/", my_bookings_page, name="my-bookings-page"),
    path("api/bookings/<int:pk>/cancel", BookingCancelView.as_view(), name="booking-cancel"),
]
