from unittest import skipUnless
from unittest.mock import patch
from django.apps import apps
from django.test import TestCase,TransactionTestCase,skipUnlessDBFeature
from rest_framework.test import APIClient
from accounts.models import User
from .models import Order,OrderEvent

@skipUnless(apps.is_installed('auditlog'),'RMS-23 optional audit stack must be installed')
class MenuAuditContract(TestCase):
    def test_real_menu_endpoints_capture_description_once_and_delete(self):
        from auditlog.models import AuditEvent
        user=User.objects.create_user(username='auditmenu',email='auditmenu@example.invalid',password='Test#123');user.role='Admin';user.save();c=APIClient();c.force_authenticate(user)
        r=c.post('/api/admin/menu',{'name':'Audit soup','category':'Starters','description':'Old','price':'2','available':True},format='json');self.assertEqual(r.status_code,201,r.data);pk=r.data['id']
        self.assertEqual(c.patch(f'/api/admin/menu/{pk}',{'description':'New'},format='json').status_code,200)
        self.assertEqual(c.patch(f'/api/admin/menu/{pk}',{'description':'New'},format='json').status_code,200)
        self.assertEqual(c.delete(f'/api/admin/menu/{pk}').status_code,204)
        self.assertEqual(list(AuditEvent.objects.filter(actor=user).order_by('pk').values_list('action',flat=True)),['MenuCreate','MenuUpdate','MenuDelete'])
@skipUnless(apps.is_installed('auditlog'),'RMS-23 optional audit stack must be installed')
@skipUnlessDBFeature('has_select_for_update')
class StatusAuditContract(TransactionTestCase):
    def test_status_endpoint_audit_and_rollback_before_publishing(self):
        from auditlog.models import AuditEvent
        user=User.objects.create_user(username='auditstatus',email='auditstatus@example.invalid',password='Test#123');user.role='Staff';user.save();order=Order.objects.create(customer=user,total_amount=0);c=APIClient();c.force_authenticate(user)
        url=f'/api/staff/orders/{order.pk}/status'
        self.assertEqual(c.post(url,{'status':'Preparing','expected_version':1},format='json').status_code,200)
        self.assertEqual(c.post(url,{'status':'Preparing','expected_version':1},format='json').status_code,200)
        self.assertEqual(AuditEvent.objects.filter(actor=user,action='OrderStatus').count(),1)
        with patch('auditlog.signals.record_event',side_effect=RuntimeError('audit failed')):
            with self.assertRaises(RuntimeError):c.post(url,{'status':'Served','expected_version':2},format='json')
        order.refresh_from_db();self.assertEqual((order.status,order.version),('Preparing',2));self.assertEqual(OrderEvent.objects.filter(order=order).count(),1)
