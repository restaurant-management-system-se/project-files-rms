from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.apps import apps
from django.db import close_old_connections
from django.test import TransactionTestCase,TestCase,skipUnlessDBFeature
from rest_framework.test import APIClient
from accounts.models import User
from .models import Order
from .services import change_status
class StatusPermissions(TestCase):
    def test_customer_and_anonymous_denied(self):
        c=APIClient();u=User.objects.create_user(username='statc',email='statc@example.invalid',password='Test#123');c.force_authenticate(u)
        self.assertEqual(c.get('/api/staff/orders').status_code,403);self.assertEqual(c.post('/api/staff/orders/1/status',{}).status_code,403)
        c.force_authenticate(None);self.assertEqual(c.get('/api/staff/orders').status_code,401)
@skipUnlessDBFeature('has_select_for_update')
class StatusPostgresTests(TransactionTestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='statusp',email='statusp@example.invalid',password='Test#123');self.user.role='Staff';self.user.save()
        self.order=Order.objects.create(customer=self.user,total_amount='0')
        self.c=APIClient();self.c.force_authenticate(self.user)
    def transition(self,status,version=1):return self.c.post(f'/api/staff/orders/{self.order.pk}/status',{'status':status,'expected_version':version},format='json')
    def test_forward_only_repeat_and_no_delete(self):
        self.assertEqual(self.transition('Served').status_code,409)
        self.assertEqual(self.transition('Cancelled').status_code,400)
        self.assertEqual(self.transition('Preparing').status_code,200)
        self.assertFalse(self.transition('Preparing').data['changed'])
        self.assertEqual(self.transition('Received',2).status_code,409)
        self.assertEqual(self.transition('Served',1).status_code,409)
        self.assertEqual(self.transition('Served',2).status_code,200)
        self.assertEqual(self.c.delete('/api/orders/'+str(self.order.pk)).status_code,403)
        self.order.refresh_from_db();self.assertEqual((self.order.status,self.order.version),('Served',3))
    def test_simultaneous_repeat_changes_once(self):
        barrier=Barrier(2)
        second=User.objects.create_user(username='status2',email='status2@example.invalid',password='Test#123');second.role='Staff';second.save()
        actors=[self.user,second]
        def attempt(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10);return change_status(user=actors[index],order_id=self.order.pk,status='Preparing',expected_version=1)[1]
            finally:close_old_connections()
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(attempt,range(2)))
        self.assertEqual(sorted(results),[False,True]);self.order.refresh_from_db();self.assertEqual(self.order.version,2)
        print('PostgreSQL status race: one transition, one safe repeat')
