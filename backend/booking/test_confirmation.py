from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from .models import Booking, BookingRequestKey, RestaurantTable

POSTGRES = connection.vendor == 'postgresql'


class PermissionTests(TestCase):
    def test_unauthenticated_is_401(self):
        self.assertEqual(self.client.post('/api/bookings', {}, content_type='application/json').status_code, 401)

    def test_staff_and_admin_denied_customer_flow(self):
        for role in ['Staff', 'Admin']:
            user = get_user_model().objects.create(username=role, email=f'{role}@example.invalid', role=role)
            self.client.force_login(user)
            self.assertEqual(self.client.post('/api/bookings', {}, content_type='application/json').status_code, 403)
        self.assertEqual(Booking.objects.count(), 0)

    def test_request_shape_and_spoofing_validation_without_database_write(self):
        user = get_user_model().objects.create_user("shape", email="shape@example.invalid")
        self.client.force_login(user)
        for payload in [[], [1], "text", {"customer_id": user.pk}, {"party_size": True}]:
            with self.subTest(payload=payload):
                response = self.client.post("/api/bookings", payload, content_type="application/json")
                self.assertEqual(response.status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)

    def test_session_requires_csrf(self):
        user = get_user_model().objects.create_user('csrf', email='csrf@example.invalid')
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        self.assertEqual(client.post('/api/bookings', {}, content_type='application/json').status_code, 403)


@skipUnless(POSTGRES, 'Real PostgreSQL required; SQLite is not concurrency evidence')
class ConfirmationTests(TransactionTestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user('one', email='one@example.invalid')
        self.other = get_user_model().objects.create_user('two', email='two@example.invalid')
        self.table = RestaurantTable.objects.create(table_number=1, capacity=4)
        self.start = timezone.now().replace(microsecond=0) + timedelta(days=2)
        self.payload = {'table_id': self.table.pk, 'start_at': self.start.isoformat(), 'party_size':2, 'idempotency_key':'test-key'}
        self.client.force_login(self.customer)

    def post(self, data=None):
        return self.client.post('/api/bookings', data or self.payload, content_type='application/json')

    def test_ut03_confirmation_persisted_and_correct(self):
        r = self.post()
        self.assertEqual(r.status_code, 201)
        booking = Booking.objects.get()
        self.assertEqual(r.json()['booking_id'], f'BK-{booking.pk}')
        self.assertEqual(booking.customer, self.customer)
        self.assertEqual(booking.table, self.table)
        self.assertEqual(booking.end_at, self.start + timedelta(minutes=90))
        self.assertEqual(r.json()['customer_id'], self.customer.pk)

    def test_ut04_overlap_409_and_alternatives(self):
        self.assertEqual(self.post().status_code, 201)
        self.client.force_login(self.other)
        for minutes in [-89, 0, 89]:
            with self.subTest(minutes=minutes):
                r = self.post({**self.payload, 'start_at':(self.start + timedelta(minutes=minutes)).isoformat()})
                self.assertEqual(r.status_code, 409)
                self.assertIn('alternative', r.json()['details'])
        self.assertEqual(Booking.objects.count(), 1)

    def test_adjacent_and_cancelled_bookings(self):
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.post({**self.payload, 'start_at':(self.start + timedelta(minutes=90)).isoformat(), 'idempotency_key':'adjacent'}).status_code, 201)
        Booking.objects.update(status=Booking.Status.CANCELLED)
        self.assertEqual(self.post({**self.payload, 'idempotency_key':'cancelled'}).status_code, 201)

    def test_invalid_requests_and_spoofed_customer(self):
        for extra in [{'party_size':0}, {'party_size':True}, {'party_size':2.5},
                      {'start_at':'bad'}, {'start_at':self.start.replace(tzinfo=None).isoformat()},
                      {'start_at':(timezone.now()-timedelta(days=1)).isoformat()},
                      {'customer_id':self.other.pk}, {'status':'Cancelled'},
                      {'idempotency_key':''}, {'table_id':-1}]:
            with self.subTest(extra=extra):
                self.assertEqual(self.post({**self.payload, **extra}).status_code, 400)
        self.assertEqual(self.client.post('/api/bookings', '{invalid', content_type='application/json').status_code, 400)
        self.assertEqual(self.post({**self.payload,'table_id':999999}).status_code, 404)
        self.assertEqual(Booking.objects.count(), 0)

    def test_active_capacity_rechecked_after_search(self):
        search = self.client.get('/api/tables/availability', {'start_at':self.start.isoformat(), 'party_size':2})
        self.assertTrue(search.json()['tables'])
        for updates in [{'active':False}, {'active':True,'capacity':1}]:
            RestaurantTable.objects.filter(pk=self.table.pk).update(**updates)
            self.assertEqual(self.post().status_code, 409)
        self.assertFalse(Booking.objects.exists())

    def test_idempotency_retry_changed_payload_and_customer_scope(self):
        first = self.post()
        retry = self.post()
        self.assertEqual((first.status_code, retry.status_code), (201,200))
        self.assertEqual(first.json(), retry.json())
        self.assertEqual(self.post({**self.payload,'party_size':3}).status_code, 409)
        # Even a retry after its start returns the persisted record.
        with patch('booking.services.timezone.now', return_value=self.start+timedelta(days=1)):
            self.assertEqual(self.post().status_code, 200)
        table = RestaurantTable.objects.create(table_number=2, capacity=4)
        self.assertEqual(self.post({**self.payload,'table_id':table.pk}).status_code,409)
        self.client.force_login(self.other)
        self.assertEqual(self.post({**self.payload,'table_id':table.pk}).status_code,201)
        self.assertEqual(Booking.objects.count(),2)

    def test_failed_metadata_write_rolls_back_booking(self):
        with patch('booking.services.BookingRequestKey.objects.create', side_effect=RuntimeError('injected failure')):
            with self.assertRaises(RuntimeError):
                self.post()
        self.assertEqual(Booking.objects.count(),0)
        self.assertEqual(BookingRequestKey.objects.count(),0)
        self.assertEqual(self.post().status_code,201)

    def test_real_session_valid_missing_and_invalid_csrf(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        client.get('/book/')
        token=client.cookies['csrftoken'].value
        self.assertEqual(client.post('/api/bookings',self.payload,content_type='application/json').status_code,403)
        self.assertEqual(client.post('/api/bookings',self.payload,content_type='application/json',HTTP_X_CSRFTOKEN='invalid').status_code,403)
        self.assertEqual(client.post('/api/bookings',self.payload,content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,201)

    def concurrent(self, specs):
        barrier=Barrier(2)
        # Create authenticated sessions before racing, so only booking calls race.
        clients=[]
        for user, payload in specs:
            client=Client(); client.force_login(user); clients.append((client,payload))
        def worker(spec):
            client,payload=spec
            try:
                barrier.wait(timeout=10)
                response=client.post('/api/bookings',payload,content_type='application/json')
                return response.status_code,response.json()
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(worker,clients))
        return result

    def test_simultaneous_different_customers_exactly_one_booking(self):
        result=self.concurrent([(self.customer,self.payload),(self.other,self.payload)])
        self.assertEqual(sorted(x[0] for x in result),[201,409])
        self.assertEqual(Booking.objects.filter(status='Confirmed').count(),1)
        self.assertEqual(BookingRequestKey.objects.count(),1)
        loser=next(body for code,body in result if code==409)
        self.assertIn('alternative',loser['details'])
        print('PostgreSQL simultaneous same-table booking: statuses 201,409; confirmed rows=1')

    def test_simultaneous_same_key_returns_same_booking(self):
        result=self.concurrent([(self.customer,self.payload),(self.customer,self.payload)])
        self.assertEqual(sorted(x[0] for x in result),[200,201])
        self.assertEqual(result[0][1]['booking_id'],result[1][1]['booking_id'])
        self.assertEqual(Booking.objects.count(),1)

    def test_simultaneous_key_reused_for_different_tables(self):
        table=RestaurantTable.objects.create(table_number=2,capacity=4)
        result=self.concurrent([(self.customer,self.payload),(self.customer,{**self.payload,'table_id':table.pk})])
        self.assertEqual(sorted(x[0] for x in result),[201,409])
        self.assertEqual(next(body for code,body in result if code==409)['code'],'IDEMPOTENCY_CONFLICT')
        self.assertEqual(Booking.objects.count(),1)

    def test_real_register_login_book_read_and_logout_flow(self):
        client = Client(enforce_csrf_checks=True)
        token = client.get('/api/auth/csrf').json()['csrfToken']
        registered = client.post('/api/auth/register', {
            'name': 'Booking Demo', 'email': 'booking-demo@example.invalid',
            'password': 'Unique-demo-booking-92!',
        }, content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(registered.status_code, 201)
        logged_in = client.post('/api/auth/login', {
            'identifier': 'booking-demo@example.invalid', 'password': 'Unique-demo-booking-92!',
        }, content_type='application/json', HTTP_X_CSRFTOKEN=token)
        self.assertEqual(logged_in.status_code, 200)
        token = logged_in.json()['csrfToken']
        confirmed = client.post('/api/bookings', self.payload, content_type='application/json',
                                HTTP_X_CSRFTOKEN=token)
        self.assertEqual(confirmed.status_code, 201)
        self.assertEqual(confirmed.json()['customer_id'], registered.json()['id'])
        self.assertEqual(len(client.get('/api/bookings').json()), 1)
        self.assertEqual(client.post('/api/auth/logout', {}, content_type='application/json',
                                     HTTP_X_CSRFTOKEN=token).status_code, 204)
        self.assertEqual(client.post('/api/bookings', self.payload, content_type='application/json',
                                     HTTP_X_CSRFTOKEN=token).status_code, 401)
        self.assertEqual(Booking.objects.count(), 1)
