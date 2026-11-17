from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from menu.models import MenuItem
class CartTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(email='cart@example.invalid',username='cart',password='Test#123')
        self.client=APIClient(); self.client.force_authenticate(self.user)
        self.item=MenuItem.objects.create(name='Soup',price='1.25',category='Starters')
    def test_add_edit_remove_and_total(self):
        r=self.client.post('/api/cart',{'items':[{'menu_item_id':self.item.pk,'quantity':3}]},format='json');self.assertEqual(r.status_code,200,r.data);self.assertEqual(r.data['total'],'3.75')
        self.assertEqual(self.client.get('/api/cart').data['items'][0]['quantity'],3)
        self.assertEqual(self.client.delete('/api/cart').data['items'],[])
    def test_invalid_cart_keeps_valid_contents(self):
        valid={'items':[{'menu_item_id':self.item.pk,'quantity':2}]};self.client.post('/api/cart',valid,format='json')
        for q in (0,-1,1.2,True,'2',100):
            self.assertEqual(self.client.post('/api/cart',{'items':[{'menu_item_id':self.item.pk,'quantity':q}]},format='json').status_code,400)
        self.assertEqual(self.client.post('/api/cart',{'items':[]},format='json').status_code,400)
        self.assertEqual(self.client.get('/api/cart').data['items'][0]['quantity'],2)
        self.item.available=False;self.item.save();self.assertEqual(self.client.post('/api/cart',valid,format='json').status_code,400)
    def test_cart_requires_customer_identity_and_csrf(self):
        self.user.role='Staff';self.user.save();self.assertEqual(self.client.get('/api/cart').status_code,403)
        self.client.force_authenticate(None);self.assertEqual(self.client.get('/api/cart').status_code,401)
