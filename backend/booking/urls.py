from django.urls import path
from . import views
from .customer_views import BookingCancelView, my_bookings_page

urlpatterns = [
    path("api/tables/availability", views.table_availability, name="table-availability"),
    path("book/", views.booking_page, name="booking-page"),
    path("my-bookings/", my_bookings_page, name="my-bookings-page"),
    path("api/bookings/<int:pk>/cancel", BookingCancelView.as_view(), name="booking-cancel"),
]
