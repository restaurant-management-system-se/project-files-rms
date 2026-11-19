"""RMS-28 / #29. Real PostgreSQL, service-process restart, rollback evidence.
Run: python manage.py test orders.test_durability --verbosity=2
The Django runner owns the disposable test database. Never deletes real rows.
"""
import json
import os
import socket
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from uuid import uuid4
from django.conf import settings
from django.db import connection
from django.test import Client, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.utils import timezone
from accounts.models import User
from booking.models import Booking, BookingRequestKey, RestaurantTable
from booking.services import confirm_booking
from menu.models import MenuItem
from .models import Order, OrderItem, OrderRequestKey, OrderEvent
from .services import create_order, change_status


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); return sock.getsockname()[1]


@skipUnlessDBFeature('has_select_for_update')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class DurabilityTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='durability', email='durability@example.invalid')
        self.staff = User.objects.create(username='durability-staff', email='durability-staff@example.invalid', role='Staff')
        self.table = RestaurantTable.objects.create(table_number=801, capacity=4)
        self.item = MenuItem.objects.create(name='Durable soup', category='Starters', price='2.25')
        self.booking_args = dict(user=self.user, table_id=self.table.pk, start_at=timezone.now() + timedelta(days=2), party_size=2, idempotency_key='durability-booking')
        self.order_args = dict(user=self.user, items=[{'menu_item_id': self.item.pk, 'quantity': 2}], context='takeaway', idempotency_key=uuid4())

    def test_failure_before_confirmation_commit_leaves_no_partial_rows(self):
        with patch('booking.services.BookingRequestKey.objects.create', side_effect=RuntimeError('injected before booking commit')):
            with self.assertRaises(RuntimeError): confirm_booking(**self.booking_args)
        self.assertEqual((Booking.objects.count(), BookingRequestKey.objects.count()), (0, 0))
        with patch('orders.services.OrderRequestKey.objects.create', side_effect=RuntimeError('injected before order commit')):
            with self.assertRaises(RuntimeError): create_order(**self.order_args)
        self.assertEqual((Order.objects.count(), OrderItem.objects.count(), OrderRequestKey.objects.count()), (0, 0, 0))
        booking, _ = confirm_booking(**self.booking_args)
        order, _ = create_order(**self.order_args)
        with patch('orders.events.queue_event', side_effect=RuntimeError('injected before status commit')):
            with self.assertRaises(RuntimeError): change_status(user=self.staff, order_id=order.pk, status='Preparing', expected_version=1)
        order.refresh_from_db()
        self.assertEqual((order.status, order.version, OrderEvent.objects.count()), ('Received', 1, 0))
        self.save_report('rollback', {'booking_id': booking.pk, 'order_id': order.pk, 'booking_partial_rows': 0, 'order_partial_rows': 0, 'status_after_failure': order.status, 'version_after_failure': order.version, 'outbox_rows': 0, 'passed': True})

    def save_report(self, name, report):
        target = Path(settings.BASE_DIR).parent / 'test-results'; target.mkdir(exist_ok=True)
        (target / f'RMS-28-{name}.json').write_text(json.dumps(report, indent=2))

    def test_saved_booking_order_survive_both_service_process_restarts(self):
        self.assertEqual(connection.vendor, 'postgresql')
        root = Path(settings.BASE_DIR).parent
        self.assertTrue((root / 'realtime/node_modules/socket.io').exists(), 'Run npm ci in realtime first')
        booking, _ = confirm_booking(**self.booking_args)
        order, _ = create_order(**(self.order_args | {'context': 'booking', 'booking_id': booking.pk}))
        client = Client(); client.force_login(self.user, backend='accounts.authentication.IdentifierBackend')
        session = client.session; session['last_activity'] = time.time(); session.save()
        cookie = '; '.join(f'{name}={value.value}' for name, value in client.cookies.items())
        django_port, node_port = free_port(), free_port()
        db = connection.settings_dict
        # Child uses the SAME PostgreSQL test database. No migrate, flush, seed or
        # database/container restart occurs between before/after snapshots.
        env = os.environ | {'DB_NAME': str(db['NAME']), 'DB_HOST': str(db['HOST']), 'DB_PORT': str(db['PORT']), 'DB_USER': str(db['USER']), 'DB_PASSWORD': str(db['PASSWORD']), 'DEBUG': 'True', 'ALLOWED_HOSTS': 'localhost,127.0.0.1', 'RMS_REALTIME_KEY': 'ephemeral-durability-test-key-32-characters', 'RMS_DJANGO_URL': f'http://127.0.0.1:{django_port}', 'RMS_PUBLIC_ORIGIN': f'http://127.0.0.1:{django_port}', 'PORT': str(node_port)}
        env.pop('DJANGO_SETTINGS_MODULE', None)
        processes = []
        def start():
            processes.extend([subprocess.Popen([sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{django_port}', '--noreload'], cwd=settings.BASE_DIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), subprocess.Popen(['node', 'server.js'], cwd=root / 'realtime', env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)])
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if any(p.poll() is not None for p in processes): self.fail('Child service failed to start')
                try:
                    for port in (django_port, node_port):
                        with socket.create_connection(('127.0.0.1', port), timeout=.5): pass
                    return
                except OSError: time.sleep(.1)
            self.fail('Timed out starting services')
        def stop():
            for process in processes: process.terminate()
            for process in processes:
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
            processes.clear()
        def snapshot():
            result = {}
            for name, path in [('booking', f'/api/bookings/{booking.pk}'), ('order', f'/api/orders/{order.pk}')]:
                with urlopen(Request(f'http://127.0.0.1:{django_port}' + path, headers={'Cookie': cookie}), timeout=5) as response:
                    result[name] = json.load(response)
            return result
        try:
            start(); before_pids = [p.pid for p in processes]; before = snapshot()
            stop(); connection.close(); start(); after_pids = [p.pid for p in processes]; after = snapshot()
            self.assertEqual(before, after)
            self.assertTrue(set(before_pids).isdisjoint(after_pids))
            self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
            self.save_report('restart', {'database': 'PostgreSQL test database retained', 'before_pids': before_pids, 'after_pids': after_pids, 'before': before, 'after': after, 'passed': True})
        finally: stop()
