"""RMS-24 / #27: isolated PostgreSQL HTTP load, opt-in canonical ST_10.

RMS_RUN_LOAD=1 python manage.py test orders.test_capacity --verbosity=2
Defaults: 60-second ramp + 600-second steady, 50 users. RMS_LOAD_BURST=1
runs the separate 300-second simultaneous-start variant. A shorter duration
is a smoke run and never earns the canonical acceptance label.
"""
import json
import math
import os
import platform
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from unittest import skipUnless
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from django.conf import settings
from django.db import connection
from django.test import Client, LiveServerTestCase
from django.utils import timezone
from accounts.models import User
from booking.models import RestaurantTable
from menu.models import MenuItem


@skipUnless(os.environ.get('RMS_RUN_LOAD') == '1', 'Opt-in real PostgreSQL 50-user run')
class CapacityTests(LiveServerTestCase):
    def test_st10_http_workload(self):
        self.assertEqual(connection.vendor, 'postgresql', 'SQLite cannot prove capacity')
        burst = os.environ.get('RMS_LOAD_BURST') == '1'
        ramp = 0 if burst else int(os.environ.get('RMS_LOAD_RAMP', '60'))
        steady = int(os.environ.get('RMS_LOAD_SECONDS', '300' if burst else '600'))
        users = 50
        self.assertGreater(steady, 0)
        menu = MenuItem.objects.create(name='Capacity soup', category='Starters', price='2.25')
        RestaurantTable.objects.bulk_create([RestaurantTable(table_number=i + 1, capacity=4) for i in range(50)])
        start_at = timezone.now() + timedelta(days=2)
        specs = []
        # Session/CSRF setup happens before measurement, without real customer data.
        for i in range(users):
            user = User.objects.create_user(username=f'capacity-{i}', email=f'capacity-{i}@example.invalid')
            client = Client(); client.force_login(user, backend='accounts.authentication.IdentifierBackend')
            session = client.session; session['last_activity'] = time.time(); session.save()
            csrf = client.get('/api/auth/csrf').json()['csrfToken']
            cookie = '; '.join(f'{key}={value.value}' for key, value in client.cookies.items())
            specs.append((i, cookie, csrf))
        barrier = Barrier(users)
        epoch = time.perf_counter()
        measured_start = epoch + ramp
        end = measured_start + steady
        availability = '/api/tables/availability?' + urlencode({'start_at': start_at.isoformat(), 'party_size': 2})
        def worker(spec):
            i, cookie, csrf = spec
            rng = random.Random(i)
            rows = []
            barrier.wait(timeout=30)
            if ramp: time.sleep(ramp * i / users)
            while time.perf_counter() < end:
                operation = rng.choices(['menu', 'availability', 'order'], weights=[50, 30, 20])[0]
                path = {'menu': '/api/menu', 'availability': availability, 'order': '/api/orders'}[operation]
                body = json.dumps({'items': [{'menu_item_id': menu.pk, 'quantity': 1}], 'context': 'takeaway', 'idempotency_key': str(uuid4())}).encode() if operation == 'order' else None
                req = Request(self.live_server_url + path, data=body, headers={'Cookie': cookie, 'X-CSRFToken': csrf, 'Content-Type': 'application/json'})
                before = time.perf_counter()
                try:
                    with urlopen(req, timeout=10) as response:
                        code = response.status; response.read()
                except HTTPError as error:
                    code = error.code; error.read()
                except (OSError, TimeoutError): code = 0
                after = time.perf_counter()
                rows.append({'user': i, 'operation': operation, 'phase': 'steady' if before >= measured_start else 'ramp', 'offset_s': before - epoch, 'elapsed_ms': (after - before) * 1000, 'status': code})
                # Closed workload: 50 active sessions, one request per user/second.
                time.sleep(max(0, 1 - (after - before)))
            return rows
        with ThreadPoolExecutor(max_workers=users) as pool:
            rows = [row for result in pool.map(worker, specs) for row in result]
        sample = [row for row in rows if row['phase'] == 'steady']
        self.assertTrue(sample)
        ordered = sorted(row['elapsed_ms'] for row in sample)
        n = len(sample)
        slow_ok = sum(row['elapsed_ms'] <= 2000 for row in sample) / n
        server_errors = sum(row['status'] >= 500 for row in sample) / n
        transport_errors = sum(row['status'] == 0 for row in sample)
        unexpected = [row for row in sample if row['status'] not in (200, 201)]
        report = {'issue': 27, 'test': 'ST_10', 'mode': 'simultaneous-start' if burst else 'ramp-steady', 'canonical_duration': (ramp == 0 and steady == 300) if burst else (ramp == 60 and steady == 600), 'users': users, 'ramp_s': ramp, 'steady_s': steady, 'workload_weights': {'menu': 50, 'availability': 30, 'order': 20}, 'hardware': {'platform': platform.platform(), 'cpu': platform.processor(), 'logical_cpus': os.cpu_count()}, 'dataset': {'users': users, 'tables': 50, 'menu_items': 1}, 'database': connection.vendor, 'percent_within_2s': slow_ok * 100, 'p95_ms_nearest_rank': ordered[math.ceil(.95 * n) - 1], 'http_5xx_percent': server_errors * 100, 'transport_errors': transport_errors, 'unexpected_http_responses': len(unexpected), 'observations': rows}
        output = Path(settings.BASE_DIR).parent / 'test-results'; output.mkdir(exist_ok=True)
        (output / ('RMS-24-burst.json' if burst else 'RMS-24-capacity.json')).write_text(json.dumps(report, indent=2))
        self.assertEqual(transport_errors, 0, 'Transport errors are failures, not hidden from denominator')
        self.assertFalse(unexpected, 'Valid isolated workload must succeed; inspect raw HTTP codes')
        self.assertGreaterEqual(slow_ok, .95)
        self.assertLessEqual(server_errors, .01)
