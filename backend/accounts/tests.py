from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction, connection
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from booking.models import Booking, RestaurantTable
from menu.models import MenuItem
from orders.models import Order, OrderItem


class DatabaseFoundationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('customer', 'customer@example.invalid', 'test-only-password')
        self.table = RestaurantTable.objects.create(table_number=1, capacity=4)
        self.item = MenuItem.objects.create(name='Soup', category='Starters', price=Decimal('80.00'))
        self.start = timezone.now() + timedelta(days=1)

    def booking(self, **changes):
        data = dict(customer=self.user, table=self.table, start_at=self.start,
                    end_at=self.start + timedelta(minutes=90), party_size=2)
        return Booking.objects.create(**(data | changes))

    def rejected(self, operation):
        with self.assertRaises(IntegrityError), transaction.atomic():
            operation()
            connection.check_constraints()

    def test_user_identifiers_roles_and_default(self):
        self.assertEqual(self.user.role, User.Role.CUSTOMER)
        self.assertTrue(self.user.check_password('test-only-password'))
        self.assertFalse(self.user.is_staff)
        for fields in [dict(role='Admin'), dict(role='Staff'), dict(is_staff=True), dict(is_superuser=True)]:
            with self.assertRaises(ValueError):
                User.objects.create_user('intruder', 'intruder@example.invalid', **fields)
        self.rejected(lambda: User.objects.create(username='duplicate', email='CUSTOMER@EXAMPLE.INVALID'))
        self.rejected(lambda: User.objects.create(username='empty', email=''))
        self.rejected(lambda: User.objects.filter(pk=self.user.pk).update(role='Unknown'))
        self.user.phone = '12345'
        self.user.save()
        self.rejected(lambda: User.objects.create(username='phone', email='phone@example.invalid', phone='12345'))

    def test_table_constraints(self):
        self.rejected(lambda: RestaurantTable.objects.create(table_number=1, capacity=2))
        self.rejected(lambda: RestaurantTable.objects.create(table_number=2, capacity=0))

    def test_booking_constraints_and_retention(self):
        self.rejected(lambda: self.booking(end_at=self.start))
        self.rejected(lambda: self.booking(end_at=self.start-timedelta(minutes=1)))
        self.rejected(lambda: self.booking(party_size=0))
        self.rejected(lambda: self.booking(status='Invalid'))
        b = self.booking(status='Cancelled')
        self.assertTrue(Booking.objects.filter(pk=b.pk).exists())
        with self.assertRaises(ProtectedError):
            self.table.delete()
        with self.assertRaises(ProtectedError):
            self.user.delete()

    def test_menu_constraints_and_zero_price(self):
        self.rejected(lambda: MenuItem.objects.create(name='Bad', category='Starters', price=-1))
        self.rejected(lambda: MenuItem.objects.create(name='Bad', category='', price=1))
        self.rejected(lambda: MenuItem.objects.create(name='', category='Starters', price=1))
        MenuItem.objects.create(name='Water', category='Beverages', price=0)

    def test_order_constraints_references_and_price_snapshot(self):
        self.rejected(lambda: Order.objects.create(customer=self.user, total_amount=-1))
        self.rejected(lambda: Order.objects.create(customer=self.user, total_amount=0, status='Invalid'))
        order = Order.objects.create(customer=self.user, total_amount=160)
        self.rejected(lambda: OrderItem.objects.create(order=order, menu_item=self.item, quantity=0, unit_price=80))
        self.rejected(lambda: OrderItem.objects.create(order=order, menu_item=self.item, quantity=1, unit_price=-1))
        line = OrderItem.objects.create(order=order, menu_item=self.item, quantity=2, unit_price=80)
        self.item.price = 100
        self.item.save()
        line.refresh_from_db()
        self.assertEqual(line.unit_price, Decimal('80.00'))
        with self.assertRaises(ProtectedError):
            self.item.delete()
        self.rejected(lambda: OrderItem.objects.create(order_id=999999, menu_item=self.item, quantity=1, unit_price=1))

    def test_admin_pages_reject_customer_and_staff(self):
        staff = User.objects.create(username='staff', email='staff@example.invalid', role='Staff')
        for user in [self.user, staff]:
            self.client.force_login(user)
            for url in ['/admin/accounts/user/', '/admin/accounts/user/add/', '/admin/booking/restauranttable/']:
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_admin_can_provision_staff_and_maintain_tables(self):
        owner = User.objects.create_superuser('owner', 'owner@example.invalid', 'test-only-password')
        self.client.force_login(owner)
        response = self.client.post('/admin/accounts/user/add/', {
            'username': 'newstaff', 'email': 'staff@example.invalid', 'phone': '', 'role': 'Staff',
            'password1': 'Local-Test-Password-728!', 'password2': 'Local-Test-Password-728!', '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302, response.context and response.context['adminform'].form.errors)
        staff = User.objects.get(username='newstaff')
        self.assertEqual(staff.role, 'Staff')
        self.assertFalse(staff.is_staff)
        response = self.client.post(f'/admin/booking/restauranttable/{self.table.pk}/change/',
                                    {'table_number': 1, 'capacity': 6, '_save': 'Save'})
        self.assertEqual(response.status_code, 302)
        self.table.refresh_from_db()
        self.assertEqual(self.table.capacity, 6)
        self.assertFalse(self.table.active)


class DemoSeedTests(TestCase):
    @override_settings(DEBUG=True)
    def test_seed_is_repeatable_complete_and_has_no_passwords(self):
        call_command('seed_demo', stdout=StringIO())
        models = [User, RestaurantTable, MenuItem, Booking, Order, OrderItem]
        before = {m.__name__: list(m.objects.order_by('pk').values()) for m in models}
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(before, {m.__name__: list(m.objects.order_by('pk').values()) for m in models})
        self.assertEqual(set(User.objects.values_list('role', flat=True)), {'Admin', 'Staff', 'Customer'})
        self.assertTrue(all(not u.has_usable_password() for u in User.objects.all()))
        self.assertEqual(set(MenuItem.objects.values_list('category', flat=True)), set(MenuItem.Category.values))
        self.assertTrue(MenuItem.objects.filter(available=False).exists())
        self.assertEqual(set(RestaurantTable.objects.values_list('capacity', flat=True)), {2,4,6,8})
        self.assertTrue(RestaurantTable.objects.filter(active=False).exists())
        self.assertEqual(set(Booking.objects.values_list('status', flat=True)), {'Confirmed', 'Cancelled'})
        for order in Order.objects.prefetch_related('items'):
            self.assertEqual(order.total_amount, sum(i.quantity*i.unit_price for i in order.items.all()))

    @override_settings(DEBUG=False)
    def test_seed_disabled_outside_development(self):
        with self.assertRaises(CommandError):
            call_command('seed_demo')
        self.assertEqual(User.objects.count(), 0)

    @override_settings(DEBUG=True)
    def test_reserved_user_collision_rolls_back_seed(self):
        User.objects.create_user('rms_demo_staff', 'existing@example.invalid', 'test-only-password')
        with self.assertRaises(CommandError):
            call_command('seed_demo')
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(RestaurantTable.objects.count(), 0)
