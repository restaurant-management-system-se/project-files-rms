import json,os,subprocess,sys,time
from pathlib import Path
from unittest.mock import patch
from django.conf import settings
from django.db import connection,transaction
from django.test import TransactionTestCase,LiveServerTestCase,Client,skipUnlessDBFeature,override_settings
from accounts.models import User
from .models import Order,OrderEvent
from .events import queue_event,dispatch_event
from .services import change_status
class EventTests(TransactionTestCase):
    def test_rollback_never_publishes_and_pending_is_retryable(self):
        user=User.objects.create_user(username='event',email='event@example.invalid',password='Test#123');order=Order.objects.create(customer=user,total_amount=0)
        with patch('orders.events.dispatch_event') as publish:
            with self.assertRaises(RuntimeError):
                with transaction.atomic():queue_event(order);raise RuntimeError('rollback')
            publish.assert_not_called();self.assertEqual(OrderEvent.objects.count(),0)
        with transaction.atomic():event=queue_event(order)
        self.assertFalse(dispatch_event(event.pk));self.assertIsNone(OrderEvent.objects.get(pk=event.pk).delivered_at)
    @override_settings(RMS_REALTIME_KEY='k'*32)
    def test_internal_secret_and_ownership(self):
        user=User.objects.create_user(username='internal',email='internal@example.invalid',password='Test#123');other=User.objects.create_user(username='otherinternal',email='otherinternal@example.invalid',password='Test#123');o=Order.objects.create(customer=user,total_amount=0)
        url=f'/api/internal/orders/{o.pk}/access'
        self.assertEqual(self.client.get(url).status_code,403)
        self.assertEqual(self.client.get(url,HTTP_X_RMS_KEY='k'*32,HTTP_X_RMS_ACTOR=str(other.pk)).status_code,403)
        self.assertEqual(self.client.get(url,HTTP_X_RMS_KEY='k'*32,HTTP_X_RMS_ACTOR=str(user.pk)).status_code,200)
@skipUnlessDBFeature('has_select_for_update')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],RMS_REALTIME_KEY='integration-key-that-is-at-least-32-characters')
class LiveOrderTests(LiveServerTestCase):
    def test_real_django_node_room_delivery_and_cross_customer_denial(self):
        root=Path(settings.BASE_DIR).parent
        if not(root/'realtime/node_modules/socket.io-client').exists():self.fail('Install realtime npm dependencies before PostgreSQL realtime tests.')
        owner=User.objects.create_user(username='liveowner',email='liveowner@example.invalid',password='Test#123');staff=User.objects.create_user(username='livestaff',email='livestaff@example.invalid',password='Test#123');staff.role='Staff';staff.save()
        outsider=User.objects.create_user(username='liveother',email='liveother@example.invalid',password='Test#123');order=Order.objects.create(customer=owner,total_amount=0)
        def cookie(user):
            c=Client();c.force_login(user,backend='accounts.authentication.IdentifierBackend');session=c.session;session['last_activity']=time.time();session.save();return f'{settings.SESSION_COOKIE_NAME}={c.cookies[settings.SESSION_COOKIE_NAME].value}'
        process=subprocess.Popen(['node','server.js'],cwd=root/'realtime',env=os.environ|{'PORT':'0','RMS_DJANGO_URL':self.live_server_url,'RMS_PUBLIC_ORIGIN':self.live_server_url,'RMS_REALTIME_KEY':settings.RMS_REALTIME_KEY},stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        client=None
        try:
            port=json.loads(process.stdout.readline())['port'];url=f'http://127.0.0.1:{port}'
            request={'url':url,'orderId':order.pk,'origin':self.live_server_url,'cookie':cookie(outsider),'deny':True}
            denied=subprocess.run(['node','test/live-client.js'],cwd=root/'realtime',input=json.dumps(request),capture_output=True,text=True,timeout=12);self.assertEqual((denied.returncode,denied.stdout.strip()),(0,'denied'),denied.stderr)
            owner_cookie=cookie(owner)
            request.update(cookie=owner_cookie,deny=False)
            from django.contrib.sessions.models import Session
            session_key=owner_cookie.split('=',1)[1]
            before=Session.objects.get(session_key=session_key).get_decoded()['last_activity']
            client=subprocess.Popen(['node','test/live-client.js'],cwd=root/'realtime',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);client.stdin.write(json.dumps(request));client.stdin.close();self.assertEqual(client.stdout.readline().strip(),'ready')
            with self.settings(RMS_REALTIME_INTERNAL_URL=url):change_status(user=staff,order_id=order.pk,status='Preparing',expected_version=1)
            received=json.loads(client.stdout.readline());self.assertEqual(received,{'order_id':order.pk,'status':'Preparing','version':2});client.wait(timeout=10);self.assertEqual(client.returncode,0)
            self.assertIsNotNone(OrderEvent.objects.get(order=order).delivered_at)
            self.assertEqual(Session.objects.get(session_key=session_key).get_decoded()['last_activity'],before)
            # Existing Django idle/session semantics reject expired socket credentials.
            from django.contrib.sessions.backends.db import SessionStore
            expired=SessionStore(session_key=session_key);expired['last_activity']=time.time()-settings.SESSION_IDLE_TIMEOUT;expired.save()
            request.update(deny=True)
            denied=subprocess.run(['node','test/live-client.js'],cwd=root/'realtime',input=json.dumps(request),capture_output=True,text=True,timeout=12)
            self.assertEqual((denied.returncode,denied.stdout.strip()),(0,'denied'),denied.stderr)
            print('PostgreSQL + real Node: owned room received committed version 2; other customer denied')
        finally:
            if client and client.poll() is None:client.kill();client.wait()
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait()
