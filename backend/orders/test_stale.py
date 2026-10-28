from django.test import TransactionTestCase,skipUnlessDBFeature
from rest_framework.test import APIClient
from uuid import uuid4
from accounts.models import User
from menu.models import MenuItem
from .models import Order,OrderItem
@skipUnlessDBFeature('has_select_for_update')
class StaleCartTests(TransactionTestCase):
    def test_item_sells_out_after_cart_and_direct_api_cannot_bypass(self):
        user=User.objects.create_user(username='stale',email='stale@example.invalid',password='Test#123');c=APIClient();c.force_authenticate(user)
        a=MenuItem.objects.create(name='Soup',price='2',category='Starters');b=MenuItem.objects.create(name='Tea',price='1',category='Beverages')
        items=[{'menu_item_id':a.pk,'quantity':2},{'menu_item_id':b.pk,'quantity':3}]
        self.assertEqual(c.post('/api/cart',{'items':items},format='json').status_code,200)
        a.available=False;a.save()
        request={'items':items,'context':'takeaway','idempotency_key':str(uuid4())}
        for _ in range(2):
            r=c.post('/api/orders',request,format='json');self.assertEqual(r.status_code,409,r.data);self.assertEqual(r.data['details']['unavailable_items'][0]['menu_item_id'],a.pk)
        self.assertEqual(Order.objects.count(),0);self.assertEqual(OrderItem.objects.count(),0)
        cart=c.get('/api/cart').data;self.assertFalse(cart['items'][0]['available']);self.assertEqual(cart['items'][1]['quantity'],3)
        request['items']=[items[1]];request['idempotency_key']=str(uuid4());self.assertEqual(c.post('/api/orders',request,format='json').status_code,201)
