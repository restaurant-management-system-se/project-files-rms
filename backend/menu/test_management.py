from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from accounts.models import User
from .models import MenuItem
from orders.models import Order, OrderItem

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class MenuTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='adminm', email='adminm@example.invalid', password='Test#123')
        self.admin.role='Admin'; self.admin.save()
        self.customer = User.objects.create_user(username='custm', email='custm@example.invalid', password='Test#123', role='Customer')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.data = {'name':'Soup', 'description':'Hot', 'price':'5.25', 'category':'Starters', 'available':True}
    def test_create_edit_delete(self):
        r=self.client.post('/api/admin/menu', self.data, format='json'); self.assertEqual(r.status_code,201,r.data)
        pk=r.data['id']; self.assertEqual(self.client.patch(f'/api/admin/menu/{pk}',{'price':'6.00'},format='json').status_code,200)
        self.assertEqual(MenuItem.objects.get(pk=pk).price,6)
        self.assertEqual(self.client.delete(f'/api/admin/menu/{pk}').status_code,204)
    def test_invalid_and_permissions(self):
        for changes in ({'price':'-1'},{'price':'NaN'},{'name':'   '},{'category':'Other'},{'price':'1.001'},{'id':123}):
            r=self.client.post('/api/admin/menu',self.data|changes,format='json'); self.assertEqual(r.status_code,400,r.data)
        for role in ('Customer','Staff'):
            self.customer.role=role; self.customer.save(); self.client.force_authenticate(self.customer)
            self.assertEqual(self.client.post('/api/admin/menu',self.data,format='json').status_code,403)
        self.client.force_authenticate(None); self.assertEqual(self.client.post('/api/admin/menu',self.data,format='json').status_code,401)
    def test_referenced_item_is_unavailable_and_history_kept(self):
        item=MenuItem.objects.create(**self.data); order=Order.objects.create(customer=self.customer,total_amount='5.25')
        OrderItem.objects.create(order=order,menu_item=item,quantity=1,unit_price='5.25')
        self.assertEqual(self.client.delete(f'/api/admin/menu/{item.pk}').status_code,200)
        item.refresh_from_db(); self.assertFalse(item.available); self.assertEqual(order.items.count(),1)
    def test_real_session_csrf(self):
        c=APIClient(enforce_csrf_checks=True); c.force_login(self.admin,backend='accounts.authentication.IdentifierBackend')
        self.assertEqual(c.post('/api/admin/menu',self.data,format='json').status_code,403)
        token=c.get('/api/auth/csrf').data['csrfToken']
        self.assertEqual(c.post('/api/admin/menu',self.data,format='json',HTTP_X_CSRFTOKEN=token).status_code,201)
