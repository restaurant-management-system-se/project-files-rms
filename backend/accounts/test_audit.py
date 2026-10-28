from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest import skipUnless
from unittest.mock import patch

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from auditlog.models import AuditEvent
from auditlog.services import audited_change, purge_expired, record_override
from booking.models import Booking, BookingOverride, RestaurantTable
from menu.models import MenuItem
from orders.models import Order
from .models import User


class AuditTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create(username='auditadmin',email='auditadmin@example.invalid',role='Admin')
        self.staff=User.objects.create(username='auditstaff',email='auditstaff@example.invalid',role='Staff')
        self.customer=User.objects.create_user('auditcustomer',email='auditcustomer@example.invalid')

    def item(self):
        return MenuItem.objects.create(name='Dish',category='Starters',price=Decimal('100'))

    def test_menu_create_change_delete_are_attributed_and_minimal(self):
        with audited_change(self.admin):
            item=self.item()
            item.name='changed';item.save()
            item.save()  # No false mutation event.
            pk=item.pk;item.delete()
        events=list(AuditEvent.objects.order_by('id'))
        self.assertEqual([e.action for e in events],['MenuCreate','MenuUpdate','MenuDelete'])
        self.assertTrue(all(e.actor_id==self.admin.pk and e.object_id==pk and e.occurred_at for e in events))
        self.assertNotIn('name',[f.name for f in AuditEvent._meta.fields])
        self.assertNotIn('payload',[f.name for f in AuditEvent._meta.fields])
        self.assertNotIn('password',[f.name for f in AuditEvent._meta.fields])

    def test_unpersisted_menu_and_order_status_do_not_create_false_events(self):
        item=self.item()
        order=Order.objects.create(customer=self.customer,total_amount=100)
        with audited_change(self.admin):
            item.name='not saved';item.save(update_fields=['price'])
            order.status='Preparing';order.save(update_fields=['total_amount'])
        self.assertEqual(AuditEvent.objects.count(),0)

    def test_order_status_capture_and_failed_business_change_rollback(self):
        order=Order.objects.create(customer=self.customer,total_amount=100)
        with audited_change(self.staff):
            order.status='Preparing';order.save()
        event=AuditEvent.objects.get();self.assertEqual(event.action,'OrderStatus')
        self.assertEqual(event.actor_id,self.staff.pk)
        with self.assertRaises(RuntimeError):
            with audited_change(self.staff):
                order.status='Served';order.save()
                raise RuntimeError('business failure')
        order.refresh_from_db();self.assertEqual(order.status,'Preparing')
        self.assertEqual(AuditEvent.objects.count(),1)

    def test_audit_failure_rolls_back_menu(self):
        with patch('auditlog.services.AuditEvent.objects.create',side_effect=RuntimeError('audit write failed')):
            with self.assertRaises(RuntimeError):
                with audited_change(self.admin): self.item()
        self.assertEqual(MenuItem.objects.count(),0)

    def test_customer_and_staff_menu_denied_and_context_is_reset(self):
        for user in [self.customer,self.staff]:
            with self.assertRaises(PermissionDenied):
                with audited_change(user): self.item()
        self.assertEqual(MenuItem.objects.count(),0)
        self.assertEqual(AuditEvent.objects.count(),0)
        self.item()  # Seeding/non-request writes are not assigned a fake actor.
        self.assertEqual(AuditEvent.objects.count(),0)

    def test_events_are_immutable_and_actor_protected(self):
        with audited_change(self.admin): self.item()
        event=AuditEvent.objects.get()
        with self.assertRaises(PermissionError): event.delete()
        with self.assertRaises(PermissionError): AuditEvent.objects.all().delete()
        with self.assertRaises(PermissionError): AuditEvent.objects.update(action='MenuDelete')
        event.action='MenuDelete'
        with self.assertRaises(PermissionError): event.save()
        with self.assertRaises(ProtectedError): self.admin.delete()
        self.assertEqual(AuditEvent.objects.get().action,'MenuCreate')

    def test_ninety_day_boundary_and_dry_run(self):
        now=timezone.now();boundary=now-timedelta(days=90)
        for delta in [-1,0,1]:
            AuditEvent.objects.create(actor=self.admin,action='MenuCreate',object_type='menu.MenuItem',object_id=1,
                                      occurred_at=boundary+timedelta(microseconds=delta))
        output=StringIO()
        with patch('auditlog.management.commands.audit_maintenance.timezone') as clock:
            clock.now.return_value=now
            call_command('audit_maintenance',stdout=output)
        self.assertEqual(AuditEvent.objects.count(),3)
        self.assertIn('Dry run',output.getvalue())
        self.assertEqual(purge_expired(now=now),1)
        self.assertEqual(AuditEvent.objects.count(),2)
        self.assertTrue(AuditEvent.objects.filter(occurred_at=boundary).exists())

    def test_admin_view_is_readonly_and_customer_staff_cannot_access(self):
        with audited_change(self.admin): self.item()
        event=AuditEvent.objects.get()
        model_admin=admin.site._registry[AuditEvent]
        for user in [self.customer,self.staff]:
            self.client.force_login(user)
            self.assertNotEqual(self.client.get('/admin/auditlog/auditevent/').status_code,200)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin/auditlog/auditevent/').status_code,200)
        self.assertFalse(model_admin.has_delete_permission(None))
        self.assertEqual(self.client.post(f'/admin/auditlog/auditevent/{event.pk}/delete/',{}).status_code,403)
        self.assertEqual(self.client.post('/admin/auditlog/auditevent/add/',{}).status_code,403)


@skipUnless(connection.vendor=='postgresql','Booking integration needs real PostgreSQL')
class AuditBookingTests(TransactionTestCase):
    def setUp(self):
        self.staff=User.objects.create(username='desk',email='desk@example.invalid',role='Staff')
        self.customer=User.objects.create_user('guest',email='guest@example.invalid')
        self.table=RestaurantTable.objects.create(table_number=1,capacity=4)
        self.client.force_login(self.staff)
        self.payload={'customer_id':self.customer.pk,'table_id':self.table.pk,
                      'start_at':(timezone.now()+timedelta(days=1)).isoformat(),'party_size':2,
                      'idempotency_key':'audit-create','reason':'Assisted booking'}

    def create(self):
        return self.client.post('/api/staff/bookings',self.payload,content_type='application/json')

    def test_real_booking_create_cancel_and_retry_event_completeness(self):
        response=self.create();self.assertEqual(response.status_code,201)
        self.assertEqual(self.create().status_code,200)
        self.assertEqual(AuditEvent.objects.count(),1)
        pk=response.json()['id'];url=f'/api/staff/bookings/{pk}/cancel'
        for _ in range(2):
            self.assertEqual(self.client.post(url,{'reason':'Requested'},content_type='application/json').status_code,200)
        self.assertEqual(list(AuditEvent.objects.order_by('id').values_list('action',flat=True)),['BookingCreate','BookingCancel'])
        self.assertEqual(AuditEvent.objects.filter(actor=self.staff,object_id=pk).count(),2)
        for override in BookingOverride.objects.all():
            with transaction.atomic(): record_override(override)
        self.assertEqual(AuditEvent.objects.count(),2)

    def test_central_audit_failure_rolls_back_booking_override_and_status(self):
        with patch('auditlog.signals.record_override',side_effect=RuntimeError('central audit unavailable')):
            with self.assertRaises(RuntimeError): self.create()
        self.assertEqual(Booking.objects.count(),0)
        self.assertEqual(BookingOverride.objects.count(),0)
        first=self.create();pk=first.json()['id']
        with patch('auditlog.signals.record_override',side_effect=RuntimeError('central audit unavailable')):
            with self.assertRaises(RuntimeError):
                self.client.post(f'/api/staff/bookings/{pk}/cancel',{'reason':'Requested'},content_type='application/json')
        self.assertEqual(Booking.objects.get().status,'Confirmed')
        self.assertEqual(AuditEvent.objects.count(),1)

    def test_retention_command_backfills_missing_events_idempotently(self):
        with patch('auditlog.signals.record_override'):
            self.assertEqual(self.create().status_code,201)
        self.assertEqual(AuditEvent.objects.count(),0)
        for _ in range(2): call_command('audit_maintenance','--execute','--backfill',stdout=StringIO())
        self.assertEqual(AuditEvent.objects.count(),1)
