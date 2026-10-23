from datetime import timedelta
from time import perf_counter

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from .availability import availability
from .models import Booking, RestaurantTable


class AvailabilityTests(TestCase):
    def setUp(self):
        self.now = timezone.now().replace(microsecond=0)
        self.start = self.now + timedelta(days=2)
        self.customer = get_user_model().objects.create_user('guest', email='guest@example.invalid')
        self.table = RestaurantTable.objects.create(table_number=1, capacity=4)

    def reserve(self, start=None, end=None, status=Booking.Status.CONFIRMED):
        return Booking.objects.create(customer=self.customer, table=self.table,
            start_at=start or self.start, end_at=end or self.start + timedelta(minutes=90),
            party_size=2, status=status)

    def test_ut01_filters_capacity_active_and_overlap(self):
        RestaurantTable.objects.create(table_number=2, capacity=1)
        RestaurantTable.objects.create(table_number=3, capacity=8, active=False)
        self.assertEqual(len(availability(self.start, 4)['tables']), 1)
        self.reserve()
        self.assertEqual(availability(self.start, 2)['tables'], [])
        self.assertIsNone(availability(self.start, 9)['alternative'])

    def test_adjacent_and_cancelled_intervals_are_free(self):
        self.reserve(start=self.start - timedelta(minutes=90), end=self.start)
        self.reserve(start=self.start + timedelta(minutes=90), end=self.start + timedelta(hours=3))
        self.reserve(status=Booking.Status.CANCELLED)
        self.assertEqual(len(availability(self.start, 2)['tables']), 1)

    def test_nearest_tie_uses_earlier_start(self):
        self.reserve()
        result = availability(self.start + timedelta(minutes=0), 2)
        self.assertEqual(result['alternative']['start_at'], self.start - timedelta(minutes=90))

    def test_nearest_merges_busy_intervals_and_crosses_day(self):
        self.reserve(start=self.now, end=self.start + timedelta(days=1))
        self.reserve(start=self.start, end=self.start + timedelta(days=2))
        result = availability(self.start, 2, now=self.now)
        self.assertEqual(result['alternative']['start_at'], self.start + timedelta(days=2))

    def test_nearest_sorts_tables_deterministically(self):
        other = RestaurantTable.objects.create(table_number=2, capacity=6)
        row = self.reserve()
        Booking.objects.create(customer=self.customer, table=other, start_at=row.start_at,
            end_at=row.end_at, party_size=2)
        self.assertEqual(availability(self.start, 2)['alternative']['table_id'], self.table.pk)

    @override_settings(BOOKING_DURATION_MINUTES=60)
    def test_configurable_duration(self):
        self.assertEqual(availability(self.start, 2)['end_at'], self.start + timedelta(hours=1))

    def test_ut02_api_rejects_bad_dates_and_guest_counts(self):
        for start, guests in [(self.now.isoformat(), 2), ('bad', 2),
                             (self.start.replace(tzinfo=None).isoformat(), 2),
                             (self.start.isoformat(), 0), (self.start.isoformat(), -1),
                             (self.start.isoformat(), '2.5'), (self.start.isoformat(), 'true')]:
            with self.subTest(start=start, guests=guests):
                r = self.client.get('/api/tables/availability', {'start_at': start, 'party_size': guests})
                self.assertEqual(r.status_code, 400)
                self.assertIn('details', r.json())
        self.assertEqual(self.client.get('/api/tables/availability').status_code, 400)

    def test_public_api_and_page_timing(self):
        before = perf_counter()
        r = self.client.get('/api/tables/availability', {'start_at': self.start.isoformat(), 'party_size': 2})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['tables'][0]['table_id'], self.table.pk)
        page = self.client.get('/book/')
        self.assertContains(page, 'Check availability')
        elapsed = perf_counter() - before
        print(f'RMS-08 local API+template smoke duration: {elapsed:.4f}s (not browser/load evidence)')
        self.assertLess(elapsed, 2)
