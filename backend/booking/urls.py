from django.urls import path
from . import views

urlpatterns = [
    path("api/tables/availability", views.table_availability, name="table-availability"),
    path("book/", views.booking_page, name="booking-page"),
]
