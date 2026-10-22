from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from booking.models import Booking, RestaurantTable
from menu.models import MenuItem
from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Create repeatable development-only sample data; demo users cannot log in."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo seeding is disabled when DEBUG=False.")
        users = {}
        for role in User.Role:
            username = f"rms_demo_{role.lower()}"
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@example.invalid", "role": role},
            )
            if created:
                user.set_unusable_password()
                user.save()
            elif user.role != role or user.has_usable_password():
                raise CommandError(f"Reserved demo user {username} was modified; no data was changed.")
            users[role] = user
        tables = []
        for number, capacity in [(901, 2), (902, 4), (903, 6), (904, 8)]:
            table, _ = RestaurantTable.objects.get_or_create(
                table_number=number, defaults={"capacity": capacity, "active": number != 904},
            )
            tables.append(table)
        dishes = []
        for name, category, price, available in [
            ("RMS Demo Soup", "Starters", "80.00", True),
            ("RMS Demo Rice", "Main Course", "150.00", True),
            ("RMS Demo Dessert", "Desserts", "90.00", False),
            ("RMS Demo Juice", "Beverages", "60.00", True),
        ]:
            item, _ = MenuItem.objects.get_or_create(name=name, category=category,
                defaults={"price": Decimal(price), "available": available})
            dishes.append(item)
        customer = users[User.Role.CUSTOMER]
        # The reserved user's records are stable on reruns, including their dates.
        for table, status in [(tables[0], Booking.Status.CONFIRMED), (tables[1], Booking.Status.CANCELLED)]:
            start = (timezone.now() + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
            booking, _ = Booking.objects.get_or_create(customer=customer, table=table,
                defaults={"start_at": start, "end_at": start + timedelta(minutes=90),
                          "party_size": 2, "status": status})
            order, created = Order.objects.get_or_create(customer=customer, booking=booking,
                defaults={"status": Order.Status.RECEIVED if status == Booking.Status.CONFIRMED else Order.Status.SERVED,
                          "total_amount": Decimal("310.00")})
            if created:
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, menu_item=dishes[0], quantity=2, unit_price=Decimal("80.00")),
                    OrderItem(order=order, menu_item=dishes[1], quantity=1, unit_price=Decimal("150.00")),
                ])
        self.stdout.write(self.style.SUCCESS("Demo data ready: 3 roles, 4 tables, 4 categories, 2 bookings/orders. No login passwords created."))
