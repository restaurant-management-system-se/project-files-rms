from django.contrib import admin
from accounts.admin import RestaurantAdminOnly
from .models import RestaurantTable


@admin.register(RestaurantTable)
class RestaurantTableAdmin(RestaurantAdminOnly, admin.ModelAdmin):
    list_display = ("table_number", "capacity", "active")
    list_filter = ("active",)
    # Bookings are retained and will be managed through the booking workflow.
