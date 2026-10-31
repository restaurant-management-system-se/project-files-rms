"""Real browser -> live Django -> PostgreSQL checks, scoped below full ST_13.

Run explicitly: python manage.py test verification.browser_smoke --verbosity=2
Requires the opt-in requirements/browser binaries, PostgreSQL and RMS_BROWSER.
Never use these timings as first-time human usability evidence.
"""
import json
import os
import platform
import secrets
import subprocess
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest import SkipTest
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import override_settings
from django.utils import timezone

from booking.models import Booking, RestaurantTable
from menu.models import MenuItem
from orders.models import Order


@override_settings(DEBUG=True, ALLOWED_HOSTS=['localhost', '127.0.0.1', 'testserver'])
class BrowserSmoke(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get('RMS_BROWSER'):
            raise SkipTest('Opt-in browser suite; set RMS_BROWSER and install verification requirements.')
        if connection.vendor != 'postgresql':
            raise RuntimeError('Browser booking/checkout checks require real PostgreSQL; SQLite is not evidence.')
        super().setUpClass()

    def setUp(self):
        from playwright.sync_api import sync_playwright
        self.engine = os.environ['RMS_BROWSER']
        if self.engine not in ('chromium', 'firefox', 'chrome', 'msedge'):
            raise ValueError('RMS_BROWSER must be chromium, firefox, chrome or msedge')
        self.pw = sync_playwright().start()
        self.addCleanup(self.pw.stop)
        launcher = self.pw.firefox if self.engine == 'firefox' else self.pw.chromium
        options = {'headless': True}
        if self.engine in ('chrome', 'msedge'):
            options['channel'] = self.engine
        self.browser = launcher.launch(**options)
        self.addCleanup(self.browser.close)
        expected = os.environ.get('RMS_EXPECTED_VERSION')
        if expected and self.browser.version != expected:
            raise RuntimeError(f'Expected {expected}, launched {self.browser.version}')
        self.password = secrets.token_urlsafe(24)
        self.table = RestaurantTable.objects.create(table_number=77, capacity=4, active=True)
        self.item = MenuItem.objects.create(name='Browser test dish', category='Starters',
                                           price='12.50', available=True, description='Fresh dish')
        self.admin = get_user_model().objects.create_superuser('browser_admin', email='browser-admin@example.invalid',
                                                        password=self.password)

    def login(self, page, email):
        page.goto(self.live_server_url + '/login/')
        page.get_by_label('Email or phone').fill(email)
        page.get_by_label('Password', exact=True).fill(self.password)
        page.get_by_role('button', name='Log in', exact=True).click()
        page.wait_for_url('**/account/')

    def no_horizontal_overflow(self, page):
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),
                        'Horizontal overflow on booking page')

    def run_case(self, name, task):
        from playwright.sync_api import expect
        for viewport in ({'width': 1280, 'height': 800}, {'width': 390, 'height': 844},
                         {'width': 320, 'height': 568}):
            with self.subTest(viewport=viewport):
                context = self.browser.new_context(viewport=viewport, timezone_id='Asia/Kolkata')
                page = context.new_page()
                page.set_default_timeout(15000)
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                entry = {'case': name, 'browser': self.engine, 'actual_version': self.browser.version,
                         'viewport': viewport, 'timezone': 'Asia/Kolkata', 'database': connection.vendor,
                         'python': platform.python_version(), 'executed_at': timezone.now().isoformat(),
                         'build': os.environ.get('GITHUB_SHA') or subprocess.check_output(
                             ['git', 'rev-parse', 'HEAD'], text=True).strip(),
                         'scope': 'automated regression, not complete ST_13 or human ST_11',
                         'unexecuted_required_flows': ['staff booking/status UI', 'live tracking', 'reconnect'],
                         'status': 'Failed'}
                started = time.monotonic()
                try:
                    task(page, expect)
                    self.assertEqual(errors, [], 'Uncaught page JavaScript error')
                    entry['status'] = 'Passed'
                finally:
                    entry['elapsed_seconds'] = round(time.monotonic() - started, 3)
                    entry['page_errors'] = errors
                    directory = Path(os.environ.get('RMS_BROWSER_RESULTS', '../test-results/browser'))
                    directory.mkdir(parents=True, exist_ok=True)
                    suffix = f'{self.engine}-{name}-{viewport["width"]}'
                    page.screenshot(path=str(directory / f'{suffix}.png'), full_page=True)
                    (directory / f'{suffix}.json').write_text(json.dumps(entry, indent=2) + '\n')
                    context.close()

    def test_customer_registration_booking_cancel_and_checkout(self):
        def task(page, expect):
            email = f'customer-{uuid4().hex}@example.invalid'
            page.goto(self.live_server_url + '/register/')
            page.get_by_label('Name', exact=True).fill('Browser Customer')
            page.get_by_label('Email', exact=True).fill(email)
            page.get_by_label('Password', exact=True).fill(self.password)
            page.get_by_role('button', name='Sign up', exact=True).click()
            page.wait_for_url('**/login/')
            self.login(page, email)
            response = page.goto(self.live_server_url + '/manage/menu/')
            self.assertEqual(response.status, 403)
            page.goto(self.live_server_url + '/book/')
            start = (timezone.now() + timedelta(days=2)).astimezone().replace(second=0, microsecond=0)
            page.get_by_label('Date and time').fill(start.strftime('%Y-%m-%dT%H:%M'))
            page.get_by_label('Guests', exact=True).fill('2')
            page.get_by_role('button', name='Check availability', exact=True).click()
            button = page.get_by_role('button', name='Confirm Table 77 · 4 seats', exact=True)
            expect(button).to_be_visible()
            self.no_horizontal_overflow(page)
            button.click()
            expect(page.get_by_role('heading', name='Booking confirmed', exact=True)).to_be_visible()
            user = get_user_model().objects.get(email=email)
            booking = Booking.objects.get(customer=user)
            self.assertEqual(booking.status, 'Confirmed')
            page.get_by_role('link', name='View or cancel my booking', exact=True).click()
            page.wait_for_url('**/my-bookings/')
            self.no_horizontal_overflow(page)
            page.on('dialog', lambda dialog: dialog.accept())
            page.get_by_role('button', name='Cancel booking', exact=True).click()
            expect(page.locator('[data-status]')).to_have_text('Cancelled')
            booking.refresh_from_db()
            self.assertEqual(booking.status, 'Cancelled')
            page.goto(self.live_server_url + '/menu/')
            expect(page.get_by_role('heading', name='Browser test dish', exact=True)).to_be_visible()
            page.get_by_role('link', name='Add to cart', exact=True).click()
            expect(page.get_by_label('Quantity for Browser test dish')).to_have_value('1')
            page.get_by_role('button', name='Place order', exact=True).click()
            expect(page.locator('#message')).to_contain_text('confirmed: Received, total 12.50')
            self.assertEqual(Order.objects.get(customer=user).total_amount, Decimal('12.50'))
            page.goto(self.live_server_url + '/account/')
            page.get_by_role('button', name='Log out', exact=True).click()
            page.wait_for_url('**/login/')
            self.assertEqual(page.goto(self.live_server_url + '/my-bookings/').status, 401)
        self.run_case('customer', task)

    def test_booking_errors_and_admin_menu(self):
        def task(page, expect):
            page.goto(self.live_server_url + '/book/')
            page.get_by_label('Date and time').fill('2001-01-01T19:00')
            page.get_by_role('button', name='Check availability', exact=True).click()
            expect(page.locator('#start-error')).to_have_text('Choose a future date and time.')
            expect(page.locator('#start')).to_have_attribute('aria-invalid', 'true')
            future = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M')
            page.get_by_label('Date and time').fill(future)
            page.get_by_label('Guests', exact=True).fill('0')
            self.assertFalse(page.locator('#guests').evaluate('(el) => el.checkValidity()'))
            self.no_horizontal_overflow(page)
            self.login(page, self.admin.email)
            page.goto(self.live_server_url + '/manage/menu/')
            name = f'Admin dish {uuid4().hex[:8]}'
            page.get_by_label('Name', exact=True).fill(name)
            page.get_by_label('Description', exact=True).fill('Browser-created dish')
            page.get_by_label('Price', exact=True).fill('5.25')
            page.get_by_role('button', name='Save item', exact=True).click()
            expect(page.locator('#message')).to_have_text('Saved')
            expect(page.locator('#items')).to_contain_text(name)
            self.assertEqual(MenuItem.objects.get(name=name).price, Decimal('5.25'))
        self.run_case('errors-admin', task)
