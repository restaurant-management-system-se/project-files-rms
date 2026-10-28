from unittest.mock import patch
from uuid import uuid4
from django.db import connection,close_old_connections
from django.test import TestCase,TransactionTestCase,skipUnlessDBFeature,override_settings
from rest_framework.test import APIClient
from accounts.models import User
from menu.models import MenuItem
from .models import Order,OrderItem
from .services import create_order
class CheckoutValidationTests(TestCase):
    def test_strict_request_validation_and_permissions(self):
        c=APIClient();u=User.objects.create_user(username='checkout',email='checkout@example.invalid',password='Test#123');c.force_authenticate(u)
        for data in ({},{'items':[],'context':'takeaway','idempotency_key':str(uuid4())},{'items':[{'menu_item_id':1,'quantity':1,'price':'0'}],'context':'takeaway','idempotency_key':str(uuid4())}):
            self.assertEqual(c.post('/api/orders',data,format='json').status_code,400)
        u.role='Staff';u.save();self.assertEqual(c.post('/api/orders',{},format='json').status_code,403)

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
@skipUnlessDBFeature('has_select_for_update')
class CheckoutPostgresTests(TransactionTestCase):
    def setUp(self):
        self.user=User.objects.create_user(username='orderp',email='orderp@example.invalid',password='Test#123')
        self.item=MenuItem.objects.create(name='Soup',category='Starters',price='2.25')
        self.c=APIClient();self.c.force_authenticate(self.user)
        self.data={'items':[{'menu_item_id':self.item.pk,'quantity':3}],'context':'takeaway','idempotency_key':str(uuid4())}
    def test_commit_price_snapshot_retry_and_owner_read(self):
        r=self.c.post('/api/orders',self.data,format='json');self.assertEqual(r.status_code,201,r.data);self.assertEqual(r.data['total_amount'],'6.75')
        self.assertEqual(self.c.post('/api/orders',self.data,format='json').status_code,200);self.assertEqual(Order.objects.count(),1)
        self.item.price='9';self.item.save();self.assertEqual(self.c.get('/api/orders/'+str(r.data['id'])).data['items'][0]['unit_price'],'2.25')
        other=User.objects.create_user(username='otherp',email='otherp@example.invalid',password='Test#123');self.c.force_authenticate(other);self.assertEqual(self.c.get('/api/orders/'+str(r.data['id'])).status_code,403)
    def test_rollback_and_unavailable(self):
        with patch('orders.services.OrderItem.objects.bulk_create',side_effect=RuntimeError('write failed')):
            with self.assertRaises(RuntimeError):self.c.post('/api/orders',self.data,format='json')
        self.assertEqual(Order.objects.count(),0)
        self.item.available=False;self.item.save();self.assertEqual(self.c.post('/api/orders',self.data,format='json').status_code,409);self.assertEqual(OrderItem.objects.count(),0)
    def test_same_key_concurrent_orders_create_once(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        barrier=Barrier(2)
        def attempt():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return create_order(user=self.user,items=self.data['items'],context='takeaway',idempotency_key=self.data['idempotency_key'])[1]
            finally:close_old_connections()
        with ThreadPoolExecutor(2) as pool: results=list(pool.map(lambda _:attempt(),range(2)))
        self.assertEqual(sorted(results),[False,True]);self.assertEqual(Order.objects.count(),1)
        print('PostgreSQL checkout retry race: one committed order, one replay')
