from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from .cancellation import cancel_own_booking
from .models import Booking, RestaurantTable
from .services import BookingError


class CancellationBoundaryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('cancel', email='cancel@example.invalid')

    def test_anonymous_role_and_csrf_guards(self):
        self.assertEqual(self.client.post('/api/bookings/1/cancel', {}, content_type='application/json').status_code, 401)
        for role in ['Staff', 'Admin']:
            user = get_user_model().objects.create(username=role, email=f'{role}@example.invalid', role=role)
            self.client.force_login(user)
            self.assertEqual(self.client.post('/api/bookings/1/cancel', {}, content_type='application/json').status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post('/api/bookings/1/cancel', {}, content_type='application/json').status_code, 403)

    def test_payload_and_method_allowlist(self):
        self.client.force_login(self.user)
        for payload in [[], 'bad', {'customer_id': self.user.pk}, {'status': 'Cancelled'}, {'reason': 'override'}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/api/bookings/1/cancel', payload, content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post('/api/bookings/1/cancel', '{bad', content_type='application/json').status_code, 400)
        for method in ['get', 'put']:
            self.assertEqual(getattr(self.client, method)('/api/bookings/1/cancel').status_code, 405)
        # Preserve the shared permission's explicit DELETE denial.
        self.assertEqual(self.client.delete('/api/bookings/1/cancel').status_code, 403)

    def test_page_is_owned_paginated_and_escaped(self):
        self.assertEqual(self.client.get('/my-bookings/').status_code, 401)
        table = RestaurantTable.objects.create(table_number=1, capacity=4)
        other = get_user_model().objects.create_user('other', email='other@example.invalid')
        start = timezone.now() + timedelta(days=1)
        for i in range(26):
            Booking.objects.create(customer=self.user, table=table, start_at=start+timedelta(days=i),
                                   end_at=start+timedelta(days=i,hours=1), party_size=2)
        private = Booking.objects.create(customer=other, table=table, start_at=start, end_at=start+timedelta(hours=1),party_size=2)
        self.client.force_login(self.user)
        response = self.client.get('/my-bookings/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page']), 25)
        self.assertNotIn(private.pk, [b.pk for b in response.context['page']])
        self.assertEqual(len(self.client.get('/my-bookings/?page=2').context['page']), 1)
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertEqual(response['Cache-Control'].find('no-store') >= 0, True)
        self.assertEqual(self.client.get('/book/').status_code, 200)

    @skipUnless(connection.vendor != 'postgresql', 'SQLite-specific fail-closed check')
    def test_sqlite_mutation_is_refused(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/bookings/1/cancel', {}, content_type='application/json')
        self.assertEqual(response.status_code, 503)


@skipUnless(connection.vendor == 'postgresql', 'Real PostgreSQL required for cancellation locks')
class CancellationPostgresTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('owner', email='owner@example.invalid')
        self.other = get_user_model().objects.create_user('other', email='other@example.invalid')
        self.table = RestaurantTable.objects.create(table_number=1, capacity=4)
        self.now = timezone.now().replace(microsecond=0)
        self.start = self.now + timedelta(days=1)
        self.booking = Booking.objects.create(customer=self.user, table=self.table, start_at=self.start,
                                               end_at=self.start+timedelta(minutes=90), party_size=2)
        self.url = f'/api/bookings/{self.booking.pk}/cancel'
        self.client.force_login(self.user)

    def cancel(self, client=None):
        return (client or self.client).post(self.url, {}, content_type='application/json')

    def test_ut05_ut21_exact_cutoff_and_offsets(self):
        for seconds, expected in [(1801,200),(1800,200),(1799,409),(0,409),(-1,409)]:
            with self.subTest(seconds=seconds):
                Booking.objects.filter(pk=self.booking.pk).update(status='Confirmed', start_at=self.now+timedelta(seconds=seconds))
                with patch('booking.cancellation.timezone') as clock:
                    clock.now.return_value = self.now
                    response = self.cancel()
                self.assertEqual(response.status_code, expected)
                self.booking.refresh_from_db()
                self.assertEqual(self.booking.status, 'Cancelled' if expected == 200 else 'Confirmed')

    def test_ut23_owner_only_and_not_found(self):
        self.client.force_login(self.other)
        self.assertEqual(self.cancel().status_code, 404)
        self.assertEqual(self.client.post('/api/bookings/999999/cancel',{},content_type='application/json').status_code,404)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status,'Confirmed')

    def test_repeated_cancellation_after_cutoff_is_safe(self):
        first = self.cancel()
        with patch('booking.cancellation.timezone') as clock:
            clock.now.return_value = self.start + timedelta(days=1)
            second = self.cancel()
        self.assertEqual((first.status_code,second.status_code),(200,200))
        self.assertTrue(first.json()['changed'])
        self.assertFalse(second.json()['changed'])
        self.assertEqual(Booking.objects.count(),1)

    def test_release_preserves_history_and_can_be_rebooked(self):
        query={'start_at':self.start.isoformat(),'party_size':2}
        self.assertEqual(self.client.get('/api/tables/availability',query).json()['tables'],[])
        self.assertEqual(self.cancel().status_code,200)
        self.assertEqual(len(self.client.get('/api/tables/availability',query).json()['tables']),1)
        self.client.force_login(self.other)
        response=self.client.post('/api/bookings',dict(query,table_id=self.table.pk,idempotency_key='rebook'),content_type='application/json')
        self.assertEqual(response.status_code,201)
        self.assertEqual(Booking.objects.count(),2)
        self.assertEqual(Booking.objects.filter(status='Cancelled').count(),1)

    def test_csrf_and_logout_in_real_session(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        client.get('/my-bookings/')
        token=client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.url,{},content_type='application/json',HTTP_X_CSRFTOKEN='invalid').status_code,403)
        self.assertEqual(client.post(self.url,{},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,200)
        self.assertEqual(client.post('/api/auth/logout',{},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,204)
        self.assertEqual(client.post(self.url,{},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,401)

    def test_commit_failure_rolls_back_status(self):
        original=Booking.save
        def failed_save(record,*args,**kwargs):
            original(record,*args,**kwargs)
            raise RuntimeError('injected after status write')
        with patch.object(Booking,'save',failed_save):
            with self.assertRaises(RuntimeError): self.cancel()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status,'Confirmed')

    def test_inactive_customer_revalidated_by_service(self):
        get_user_model().objects.filter(pk=self.user.pk).update(is_active=False)
        with self.assertRaises(BookingError) as error:
            cancel_own_booking(user=self.user,booking_id=self.booking.pk)
        self.assertEqual(error.exception.status,403)

    def race(self,operations):
        clients=[]
        for user,method,url,payload in operations:
            client=Client();client.force_login(user);clients.append((client,method,url,payload))
        barrier=Barrier(2)
        def worker(spec):
            client,method,url,payload=spec
            try:
                barrier.wait(timeout=10)
                response=getattr(client,method)(url,payload,content_type='application/json')
                return response.status_code,response.json()
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker,clients))

    def test_simultaneous_cancellations_change_once(self):
        results=self.race([(self.user,'post',self.url,{}),(self.user,'post',self.url,{})])
        self.assertEqual([r[0] for r in results],[200,200])
        self.assertEqual(sorted(r[1]['changed'] for r in results),[False,True])
        self.assertEqual(Booking.objects.count(),1)
        self.assertEqual(Booking.objects.get().status,'Cancelled')
        print('PostgreSQL cancellation race: 200,200; exactly one status transition; history rows=1')

    def test_cancellation_and_confirmation_serialize_on_table(self):
        payload={'table_id':self.table.pk,'start_at':self.start.isoformat(),'party_size':2,'idempotency_key':'race-rebook'}
        results=self.race([(self.user,'post',self.url,{}),(self.other,'post','/api/bookings',payload)])
        self.assertEqual(results[0][0],200)
        self.assertIn(results[1][0],[201,409])
        client=Client();client.force_login(self.other)
        retry=client.post('/api/bookings',payload,content_type='application/json')
        self.assertIn(retry.status_code,[200,201])
        self.assertEqual(Booking.objects.filter(status='Confirmed').count(),1)
        self.assertEqual(Booking.objects.filter(status='Cancelled').count(),1)
        print('PostgreSQL cancel/rebook race: serialized; one confirmed row plus retained cancelled row')
