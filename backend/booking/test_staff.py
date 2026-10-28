from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection, connections
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from .models import Booking, BookingOverride, RestaurantTable


class StaffReadTests(TestCase):
    def setUp(self):
        U=get_user_model()
        self.staff=U.objects.create(username='desk',email='desk@example.invalid',role='Staff')
        self.admin=U.objects.create(username='admin',email='admin@example.invalid',role='Admin')
        self.customer=U.objects.create_user('guest',email='guest@example.invalid')
        self.table=RestaurantTable.objects.create(table_number=7,capacity=4)
        self.start=timezone.now()+timedelta(days=1)
        self.booking=Booking.objects.create(customer=self.customer,table=self.table,start_at=self.start,end_at=self.start+timedelta(minutes=90),party_size=2)

    def test_auth_role_and_csrf(self):
        paths=['/api/staff/bookings','/staff/bookings/']
        for p in paths: self.assertEqual(self.client.get(p).status_code,401)
        self.client.force_login(self.customer)
        for p in paths: self.assertEqual(self.client.get(p).status_code,403)
        self.assertEqual(self.client.post('/api/staff/bookings',{},content_type='application/json').status_code,403)
        self.assertEqual(self.client.post(f'/api/staff/bookings/{self.booking.pk}/cancel',{'reason':'x'},content_type='application/json').status_code,403)
        client=Client(enforce_csrf_checks=True);client.force_login(self.staff)
        self.assertEqual(client.post('/api/staff/bookings',{},content_type='application/json').status_code,403)

    def test_search_reference_customer_table_date_status_and_invalid(self):
        self.client.force_login(self.staff)
        for query in [{'q':f'BK-{self.booking.pk}'},{'q':'guest@example.invalid'},{'q':'7'},
                      {'date':self.start.date().isoformat(),'status':'Confirmed'},{'date':'','status':''}]:
            with self.subTest(query=query):
                response=self.client.get('/api/staff/bookings',query)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json()['count'],1)
        self.assertEqual(self.client.get('/api/staff/bookings',{'status':'Cancelled'}).json()['count'],0)
        for query in [{'date':'bad'},{'status':'bad'},{'page':0}]:
            self.assertEqual(self.client.get('/api/staff/bookings',query).status_code,400)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/api/staff/bookings').status_code,200)

    def test_validation_and_no_delete_or_customer_create_regression(self):
        self.client.force_login(self.staff)
        for data in [[],{}, {'reason':' '},{'reason':'x','status':'Cancelled'}]:
            self.assertEqual(self.client.post(f'/api/staff/bookings/{self.booking.pk}/cancel',data,content_type='application/json').status_code,400)
        self.assertEqual(self.client.post('/api/bookings',{},content_type='application/json').status_code,403)
        for path in ['/api/staff/bookings',f'/api/staff/bookings/{self.booking.pk}/cancel']:
            self.assertEqual(self.client.delete(path).status_code,405)
        self.assertEqual(self.client.delete(f'/api/bookings/{self.booking.pk}').status_code,403)
        self.assertEqual(Booking.objects.count(),1)

    def test_dashboard_paginates_and_escapes_audit(self):
        self.customer.first_name='<script>bad()</script>';self.customer.save()
        BookingOverride.objects.create(actor=self.staff,booking=self.booking,action='Create',reason='<img src=x onerror=bad()>')
        for i in range(25):
            Booking.objects.create(customer=self.customer,table=self.table,start_at=self.start+timedelta(days=i+1),end_at=self.start+timedelta(days=i+1,hours=1),party_size=2)
        self.client.force_login(self.staff)
        page=self.client.get('/staff/bookings/')
        self.assertEqual(page.status_code,200)
        self.assertEqual(len(page.context['page']),25)
        last=self.client.get('/staff/bookings/?page=2')
        self.assertContains(last,'&lt;script&gt;')
        self.assertContains(last,'&lt;img src=x onerror=bad()&gt;')
        self.assertNotContains(last,'<img src=x onerror=bad()>')
        self.assertContains(page,'csrfmiddlewaretoken')
        self.assertIn('no-store',page['Cache-Control'])


@skipUnless(connection.vendor=='postgresql','Real PostgreSQL required for staff booking locks')
class StaffPostgresTests(TransactionTestCase):
    def setUp(self):
        U=get_user_model()
        self.staff=U.objects.create(username='desk',email='desk@example.invalid',role='Staff')
        self.admin=U.objects.create(username='admin',email='admin@example.invalid',role='Admin')
        self.customer=U.objects.create_user('guest',email='guest@example.invalid')
        self.other=U.objects.create_user('other',email='other@example.invalid')
        self.table=RestaurantTable.objects.create(table_number=1,capacity=4)
        self.start=timezone.now().replace(microsecond=0)+timedelta(days=1)
        self.payload={'customer_id':self.customer.pk,'table_id':self.table.pk,'start_at':self.start.isoformat(),
                      'party_size':2,'idempotency_key':'manual-1','reason':'Walk-in requested by customer'}
        self.client.force_login(self.staff)

    def create(self,data=None):
        return self.client.post('/api/staff/bookings',data or self.payload,content_type='application/json')

    def cancel(self,pk,reason='Customer requested staff override'):
        return self.client.post(f'/api/staff/bookings/{pk}/cancel',{'reason':reason},content_type='application/json')

    def test_manual_create_retry_and_audit(self):
        first=self.create();retry=self.create()
        self.assertEqual((first.status_code,retry.status_code),(201,200))
        self.assertEqual(first.json()['booking_id'],retry.json()['booking_id'])
        event=BookingOverride.objects.get()
        self.assertEqual((event.actor_id,event.action,event.reason),(self.staff.pk,'Create',self.payload['reason']))
        self.assertEqual(event.booking.customer_id,self.customer.pk)
        self.assertEqual(self.create({**self.payload,'reason':'changed'}).status_code,409)
        self.assertEqual(Booking.objects.count(),1)

    def test_staff_cancel_inside_customer_cutoff_and_repeat(self):
        booking=Booking.objects.create(customer=self.customer,table=self.table,start_at=timezone.now()+timedelta(minutes=5),end_at=timezone.now()+timedelta(hours=1),party_size=2)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(f'/api/bookings/{booking.pk}/cancel',{},content_type='application/json').status_code,409)
        self.client.force_login(self.admin)
        first=self.cancel(booking.pk);retry=self.cancel(booking.pk)
        self.assertEqual((first.status_code,retry.status_code),(200,200))
        self.assertFalse(retry.json()['changed'])
        self.assertEqual(Booking.objects.count(),1)
        event=BookingOverride.objects.get()
        self.assertEqual(event.actor_id,self.admin.pk)
        self.assertEqual(event.action,'Cancel')

    def test_customer_cancel_staff_search_and_rebook(self):
        first=self.create();self.assertEqual(first.status_code,201)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(f'/api/bookings/{first.json()["id"]}/cancel',{},content_type='application/json').status_code,200)
        self.client.force_login(self.staff)
        results=self.client.get('/api/staff/bookings',{'status':'Cancelled'}).json()
        self.assertEqual(results['count'],1)
        self.assertEqual(self.create({**self.payload,'idempotency_key':'rebook'}).status_code,201)
        self.assertEqual(Booking.objects.filter(status='Confirmed').count(),1)
        self.assertEqual(Booking.objects.filter(status='Cancelled').count(),1)

    def test_overlap_capacity_active_customer_and_payload_validation(self):
        for delta in [{'customer_id':self.staff.pk},{'customer_id':999999}]:
            self.assertEqual(self.create({**self.payload,**delta}).status_code,404)
        for delta in [{'reason':' '},{'reason':'x'*501},{'party_size':True},{'party_size':0},{'status':'Cancelled'},
                      {'start_at':self.start.replace(tzinfo=None).isoformat()}, {'start_at':(timezone.now()-timedelta(days=1)).isoformat()}]:
            self.assertEqual(self.create({**self.payload,**delta}).status_code,400)
        for updates in [{'active':False},{'active':True,'capacity':1}]:
            RestaurantTable.objects.filter(pk=self.table.pk).update(**updates)
            self.assertEqual(self.create().status_code,409)
        RestaurantTable.objects.filter(pk=self.table.pk).update(active=True,capacity=4)
        self.assertEqual(self.create().status_code,201)
        self.assertEqual(self.create({**self.payload,'idempotency_key':'overlap'}).status_code,409)
        self.assertEqual(self.create({**self.payload,'idempotency_key':'adjacent','start_at':(self.start+timedelta(minutes=90)).isoformat()}).status_code,201)

    def test_audit_failure_rolls_back_create_and_cancel(self):
        with patch('booking.staff_services.BookingOverride.objects.create',side_effect=RuntimeError('audit failed')):
            with self.assertRaises(RuntimeError): self.create()
        self.assertEqual(Booking.objects.count(),0)
        first=self.create();self.assertEqual(first.status_code,201)
        with patch('booking.staff_services.BookingOverride.objects.create',side_effect=RuntimeError('audit failed')):
            with self.assertRaises(RuntimeError): self.cancel(first.json()['id'])
        self.assertEqual(Booking.objects.get().status,'Confirmed')
        self.assertEqual(BookingOverride.objects.count(),1)

    def test_real_csrf_logout_and_inactive_staff(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.staff)
        client.get('/staff/bookings/');token=client.cookies['csrftoken'].value
        self.assertEqual(client.post('/api/staff/bookings',self.payload,content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,201)
        self.assertEqual(client.post('/api/auth/logout',{},content_type='application/json',HTTP_X_CSRFTOKEN=token).status_code,204)
        self.assertEqual(client.get('/api/staff/bookings').status_code,401)
        get_user_model().objects.filter(pk=self.staff.pk).update(is_active=False)
        self.assertEqual(self.create().status_code,401)

    def race(self,specs):
        clients=[]
        for user,url,payload in specs:
            client=Client();client.force_login(user);clients.append((client,url,payload))
        barrier=Barrier(2)
        def worker(spec):
            client,url,payload=spec
            try:
                barrier.wait(timeout=10)
                response=client.post(url,payload,content_type='application/json')
                return response.status_code,response.json()
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool: return list(pool.map(worker,clients))

    def test_staff_vs_customer_same_table_only_one_commits(self):
        payload={k:v for k,v in self.payload.items() if k not in ['customer_id','reason']}
        results=self.race([(self.staff,'/api/staff/bookings',self.payload),(self.other,'/api/bookings',payload)])
        self.assertEqual(sorted(r[0] for r in results),[201,409])
        self.assertEqual(Booking.objects.filter(status='Confirmed').count(),1)
        print('PostgreSQL staff/customer same-table race: 201,409; confirmed rows=1')

    def test_staff_same_key_race_one_booking_and_one_audit(self):
        results=self.race([(self.staff,'/api/staff/bookings',self.payload)]*2)
        self.assertEqual(sorted(r[0] for r in results),[200,201])
        self.assertEqual(Booking.objects.count(),1)
        self.assertEqual(BookingOverride.objects.count(),1)

    def test_customer_vs_staff_cancel_serializes_without_duplicate_override(self):
        first=self.create();pk=first.json()['id']
        results=self.race([(self.customer,f'/api/bookings/{pk}/cancel',{}),
                           (self.staff,f'/api/staff/bookings/{pk}/cancel',{'reason':'Assisted cancellation'})])
        self.assertEqual([r[0] for r in results],[200,200])
        self.assertEqual(sorted(r[1]['changed'] for r in results),[False,True])
        self.assertEqual(Booking.objects.get().status,'Cancelled')
        self.assertLessEqual(BookingOverride.objects.filter(action='Cancel').count(),1)
