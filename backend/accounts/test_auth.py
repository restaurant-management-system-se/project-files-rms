"""REQ-12/13/14 and scoped SEC-1/3/4/5/8 regression evidence."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from django.test import Client, RequestFactory, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from accounts.models import User
from accounts.permissions import IsOwnerOrStaffAdmin, IsRestaurantAdmin, IsStaffOrAdmin, owned_queryset
from accounts.serializers import RegistrationSerializer
from accounts.views import SessionAPIView
from booking.models import Booking, RestaurantTable
from orders.models import Order


class AuthTests(TestCase):
    password = 'Cedar#29'

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def payload(self, **changes):
        return dict(name='Test Customer', email='customer@example.invalid', phone='+919876543210',
                    password=self.password) | changes

    def token(self, client=None):
        return (client or self.client).get('/api/auth/csrf').json()['csrfToken']

    def post(self, path, data, client=None):
        client = client or self.client
        return client.post(path, data, content_type='application/json', HTTP_X_CSRFTOKEN=self.token(client))

    def register(self, **changes):
        return self.post('/api/auth/register', self.payload(**changes))

    def login(self, identifier='customer@example.invalid', password=None, client=None):
        return self.post('/api/auth/login', {'identifier': identifier, 'password': password or self.password}, client)

    def test_registration_defaults_customer_and_no_password_response(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, response.content)
        user = User.objects.get()
        self.assertEqual(user.role, 'Customer')
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(set(response.json()), {'id', 'name', 'email', 'phone', 'role'})
        self.assertNotIn(self.password, response.content.decode())

    def test_public_registration_rejects_all_escalation_fields(self):
        for field, value in [('role', 'Admin'), ('role', 'Staff'), ('is_staff', True),
                             ('is_superuser', True), ('groups', [1]), ('user_permissions', [1]), ('id', 1)]:
            with self.subTest(field=field, value=value):
                self.assertEqual(self.register(**{field: value}).status_code, 400)
                self.assertEqual(User.objects.count(), 0)

    def test_duplicate_email_case_insensitive_and_phone(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register(email='CUSTOMER@EXAMPLE.INVALID', phone='').status_code, 400)
        self.assertEqual(self.register(email='other@example.invalid').status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_optional_phone_and_required_email_preserve_model_contract(self):
        self.assertEqual(self.register(phone='').status_code, 201)
        self.assertIsNone(User.objects.get().phone)
        self.assertEqual(self.register(email='', phone='+919999999999').status_code, 400)

    def test_concurrent_duplicate_is_validation_error(self):
        serializer = RegistrationSerializer(data=self.payload())
        self.assertTrue(serializer.is_valid())
        self.register()
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            serializer.save()
        self.assertEqual(User.objects.count(), 1)

    def test_password_boundary_seven_rejected_eight_accepted(self):
        self.assertEqual(len('Cedar#2'), 7)
        self.assertEqual(self.register(password='Cedar#2').status_code, 400)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(self.register(password=self.password).status_code, 201)

    @override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.PBKDF2PasswordHasher'])
    def test_actual_pbkdf2_salts_and_no_password_in_response_or_application_logs(self):
        import logging
        output = StringIO()
        handler = logging.StreamHandler(output)
        logger = logging.getLogger()
        logger.addHandler(handler)
        try:
            first = self.register()
            second = self.register(email='other@example.invalid', phone='')
            self.login(password='wrong-password')
        finally:
            logger.removeHandler(handler)
        self.assertEqual((first.status_code, second.status_code), (201, 201))
        hashes = list(User.objects.values_list('password', flat=True))
        self.assertTrue(all(value.startswith('pbkdf2_sha256$') for value in hashes))
        self.assertNotEqual(*hashes)
        self.assertTrue(all(self.password not in value for value in hashes))
        self.assertNotIn(self.password, output.getvalue())

    def test_login_email_and_phone_rotates_session_and_csrf(self):
        self.register()
        old_token = self.token()
        # A pre-login anonymous session must not become the authenticated session.
        session = self.client.session
        session['prelogin'] = True
        session.save()
        old_session = session.session_key
        response = self.login(identifier='CUSTOMER@EXAMPLE.INVALID')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotEqual(old_session, self.client.session.session_key)
        self.assertFalse(Session.objects.filter(session_key=old_session).exists())
        self.assertNotEqual(old_token, response.json()['csrfToken'])
        self.assertEqual(self.client.get('/api/auth/session').status_code, 200)
        self.assertEqual(self.post('/api/auth/logout', {}).status_code, 204)
        self.assertEqual(self.login(identifier='+919876543210').status_code, 200)

    def test_invalid_unknown_inactive_and_sql_like_login_are_generic(self):
        self.register()
        for identifier, password in [('customer@example.invalid', 'wrong'), ('missing@example.invalid', 'wrong'),
                                     ("' OR 1=1; DROP TABLE accounts_user; --", 'wrong')]:
            response = self.login(identifier, password)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json(), {'detail': 'Invalid credentials.'})
        user = User.objects.get()
        user.is_active = False
        user.save()
        self.assertEqual(self.login().status_code, 401)
        self.assertEqual(User.objects.count(), 1)

    def test_malformed_input_and_unknown_fields_fail_safely(self):
        for change in [dict(email='not-email'), dict(phone='<script>'), dict(name=''),
                       dict(name='x'*61), dict(password='x'*129), dict(role='Admin')]:
            self.assertEqual(self.register(**change).status_code, 400)
        for body in ['{', '[]', 'null']:
            response = self.client.post('/api/auth/register', body, content_type='application/json',
                                        HTTP_X_CSRFTOKEN=self.token())
            self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_anonymous_login_and_registration_require_csrf(self):
        for endpoint, data in [('/api/auth/register', self.payload()),
                               ('/api/auth/login', {'identifier':'missing', 'password':'wrong'})]:
            for token in [None, 'invalid']:
                headers = {} if token is None else {'HTTP_X_CSRFTOKEN': token}
                response = self.client.post(endpoint, data, content_type='application/json', **headers)
                self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(self.register().status_code, 201)

    def test_authenticated_logout_csrf_missing_invalid_valid_and_replay(self):
        self.register()
        self.login()
        old_key = self.client.session.session_key
        for token in [None, 'invalid']:
            headers = {} if token is None else {'HTTP_X_CSRFTOKEN': token}
            self.assertEqual(self.client.post('/api/auth/logout', {}, **headers).status_code, 403)
            self.assertTrue(Session.objects.filter(session_key=old_key).exists())
        self.assertEqual(self.client.get('/api/auth/logout').status_code, 405)
        self.assertEqual(self.post('/api/auth/logout', {}).status_code, 204)
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        replay = Client(enforce_csrf_checks=True)
        replay.cookies[settings.SESSION_COOKIE_NAME] = old_key
        self.assertEqual(replay.get('/api/auth/session').status_code, 401)

    def test_csrf_bad_origin_and_rotated_prelogin_token_rejected(self):
        self.register()
        old_token = self.token()
        self.login()
        self.assertEqual(self.client.post('/api/auth/logout', {}, HTTP_X_CSRFTOKEN=old_token).status_code, 403)
        self.assertEqual(self.client.post('/api/auth/logout', {}, HTTP_X_CSRFTOKEN=self.token(),
                                         HTTP_ORIGIN='https://attacker.invalid').status_code, 403)

    def test_protected_api_missing_auth_401(self):
        for path in ['/api/auth/session', '/api/auth/logout', '/api/bookings', '/api/orders']:
            response = self.client.post(path, {}) if path.endswith('logout') else self.client.get(path)
            self.assertEqual(response.status_code, 401, path)

    def test_idle_boundary_before_at_after_and_replay(self):
        self.register()
        for elapsed, expected in [(1799,200), (1800,401), (1801,401)]:
            with self.subTest(elapsed=elapsed):
                self.login()
                key = self.client.session.session_key
                last = self.client.session['last_activity']
                with patch('accounts.middleware.time', return_value=last+elapsed):
                    self.assertEqual(self.client.get('/api/auth/session').status_code, expected)
                if expected == 401:
                    self.assertFalse(Session.objects.filter(session_key=key).exists())
                    self.client.cookies[settings.SESSION_COOKIE_NAME] = key
                    self.assertEqual(self.client.get('/api/auth/session').status_code, 401)

    def test_activity_resets_deadline_but_status_poll_does_not(self):
        self.register()
        self.login()
        last = self.client.session['last_activity']
        with patch('accounts.middleware.time', return_value=last+1000):
            self.assertEqual(self.client.get('/api/auth/session').status_code,200)
        self.assertEqual(self.client.session['last_activity'],last)
        with patch('accounts.middleware.time', return_value=last+1799):
            self.assertEqual(self.client.get('/account/').status_code,200)
        self.assertEqual(self.client.session['last_activity'],last+1799)
        with patch('accounts.middleware.time', return_value=last+1801):
            self.assertEqual(self.client.get('/api/auth/session').status_code,200)
        with patch('accounts.middleware.time', return_value=last+3599):
            self.assertEqual(self.client.get('/account/').status_code,401)

    def test_existing_admin_session_gets_idle_deadline(self):
        self.register()
        self.client.force_login(User.objects.get())
        self.assertEqual(self.client.get('/api/auth/session').status_code,200)

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_https_cookie_flags(self):
        self.register()
        response = self.login()
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie['secure'])
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'],'Lax')
        self.assertEqual(int(cookie['max-age']),1800)
        self.assertTrue(self.client.get('/api/auth/csrf', secure=True).cookies['csrftoken']['secure'])

    def test_form_flow_inline_validation_safe_output_and_logout(self):
        response = self.client.get('/register/')
        self.assertContains(response, 'csrfmiddlewaretoken')
        token = self.client.cookies['csrftoken'].value
        response = self.client.post('/register/',self.payload(password='short') | {'csrfmiddlewaretoken':token})
        self.assertContains(response,'at least 8 characters',status_code=400)
        self.assertNotContains(response,'value="short"',status_code=400)
        payload = self.payload(name="<script>alert('XSS')</script>")
        response = self.client.post('/register/',payload | {'csrfmiddlewaretoken':token})
        self.assertRedirects(response,'/login/')
        response = self.client.post('/login/',{'identifier':payload['email'],'password':self.password,'csrfmiddlewaretoken':token})
        self.assertRedirects(response,'/account/')
        response = self.client.get('/account/')
        self.assertContains(response,'&lt;script&gt;')
        self.assertNotContains(response,"<script>alert('XSS')</script>")
        self.assertEqual(User.objects.get().first_name,payload['name'])
        self.assertEqual(self.client.post('/logout/').status_code,403)
        token = self.client.cookies['csrftoken'].value
        self.assertRedirects(self.client.post('/logout/',{'csrfmiddlewaretoken':token}),'/login/')
        self.assertEqual(self.client.get('/account/').status_code,401)

    def test_auth_page_rejects_non_post_mutations(self):
        for path in ['/register/','/login/','/logout/']:
            self.assertEqual(self.client.put(path,HTTP_X_CSRFTOKEN=self.token()).status_code,405)


class OwnershipTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user('owner','owner@example.invalid','test-only-password')
        self.other = User.objects.create_user('other','other@example.invalid','test-only-password')
        self.staff = User.objects.create(username='staff',email='staff@example.invalid',role='Staff')
        self.admin = User.objects.create(username='admin',email='admin@example.invalid',role='Admin')
        table = RestaurantTable.objects.create(table_number=1,capacity=4)
        start = timezone.now()+timedelta(days=1)
        self.bookings = [Booking.objects.create(customer=u, table=table, start_at=start, end_at=start+timedelta(minutes=90),party_size=2)
                         for u in [self.customer,self.other]]
        self.orders = [Order.objects.create(customer=u,total_amount=0) for u in [self.customer,self.other]]

    def test_list_and_direct_object_role_matrix(self):
        for user in [self.customer,self.other,self.staff,self.admin]:
            self.client.force_login(user)
            for base, objects in [('/api/bookings',self.bookings),('/api/orders',self.orders)]:
                response = self.client.get(base)
                self.assertEqual(response.status_code,200)
                expected = objects if user.role in ['Staff','Admin'] else [o for o in objects if o.customer_id==user.pk]
                self.assertEqual([o['id'] for o in response.json()],[o.pk for o in expected])
                for obj in objects:
                    code = 200 if user.role in ['Staff','Admin'] or obj.customer_id==user.pk else 403
                    self.assertEqual(self.client.get(f'{base}/{obj.pk}').status_code,code)
        self.client.logout()
        for base in ['/api/bookings','/api/orders']:
            self.assertEqual(self.client.get(base).status_code,401)

    def test_role_permissions_and_anonymous_default_deny(self):
        request = RequestFactory().get('/')
        for user in [AnonymousUser(),self.customer,self.staff,self.admin]:
            request.user = user
            self.assertEqual(IsRestaurantAdmin().has_permission(request,None),user==self.admin)
            self.assertEqual(IsStaffOrAdmin().has_permission(request,None),user in [self.staff,self.admin])
        self.assertFalse(owned_queryset(Order.objects.all(),AnonymousUser()).exists())
        self.customer.is_active=False
        request.user=self.customer
        self.assertFalse(IsOwnerOrStaffAdmin().has_permission(request,None))

    def test_read_only_resources_never_allow_staff_hard_delete_or_customer_mutation(self):
        before_bookings=list(Booking.objects.values())
        before_orders=list(Order.objects.values())
        for user in [self.customer,self.staff,self.admin]:
            self.client.force_login(user)
            for path in [f'/api/bookings/{self.bookings[0].pk}',f'/api/orders/{self.orders[0].pk}']:
                for method in ['delete','patch','put']:
                    self.assertEqual(getattr(self.client,method)(path,{},content_type='application/json').status_code,403 if method == "delete" else 405)
        self.assertEqual(before_bookings,list(Booking.objects.values()))
        self.assertEqual(before_orders,list(Order.objects.values()))

    def test_shared_api_csrf_guard_covers_all_mutation_verbs(self):
        class Probe(SessionAPIView):
            def post(self, request):
                from rest_framework.response import Response
                return Response({'changed':True})
            put = patch = delete = post
        factory = APIRequestFactory(enforce_csrf_checks=True)
        for method in ['post','put','patch','delete']:
            request = getattr(factory,method)('/',{},format='json')
            request.user = self.customer
            response = Probe.as_view()(request)
            self.assertEqual(response.status_code,403)

    def test_role_guards_enforce_real_api_requests(self):
        from rest_framework.response import Response
        for permission, allowed in [(IsRestaurantAdmin,[self.admin]),(IsStaffOrAdmin,[self.staff,self.admin])]:
            class Probe(SessionAPIView):
                permission_classes=[permission]
                def get(self, request):
                    return Response({"allowed":True})
            for user in [AnonymousUser(),self.customer,self.staff,self.admin]:
                request=APIRequestFactory().get("/")
                request.user=user
                expected=200 if user in allowed else 403 if user.is_authenticated else 401
                self.assertEqual(Probe.as_view()(request).status_code,expected)
