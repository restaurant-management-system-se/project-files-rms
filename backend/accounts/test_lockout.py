from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.db import connection, connections
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone

from .models import LoginGuard, User

PASSWORD='Lockout-demo-874!'


class LockoutTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('guarded',email='guarded@example.invalid',phone='+919876543210',password=PASSWORD)
        self.now=timezone.now().replace(microsecond=0)

    def attempt(self,password='wrong',identifier=None):
        return authenticate(identifier=identifier or self.user.email,password=password)

    def test_fifth_failure_locks_correct_password_and_does_not_extend(self):
        with patch('accounts.authentication.timezone') as clock:
            clock.now.return_value=self.now
            for n in range(1,6):
                self.assertIsNone(self.attempt())
                guard=LoginGuard.objects.get(user=self.user)
                self.assertEqual(guard.failures,n)
                self.assertEqual(guard.locked_until,self.now+timedelta(minutes=15) if n==5 else None)
            clock.now.return_value=self.now+timedelta(minutes=1)
            self.assertIsNone(self.attempt(PASSWORD))
            self.assertIsNone(self.attempt())
        guard.refresh_from_db()
        self.assertEqual(guard.locked_until,self.now+timedelta(minutes=15))

    def test_exact_expiry_and_pre_boundary(self):
        LoginGuard.objects.create(user=self.user,failures=5,locked_until=self.now+timedelta(minutes=15))
        with patch('accounts.authentication.timezone') as clock:
            clock.now.return_value=self.now+timedelta(minutes=15)-timedelta(microseconds=1)
            self.assertIsNone(self.attempt(PASSWORD))
            clock.now.return_value=self.now+timedelta(minutes=15)
            self.assertEqual(self.attempt(PASSWORD),self.user)
        guard=LoginGuard.objects.get(user=self.user)
        self.assertEqual(guard.failures,0);self.assertIsNone(guard.locked_until)

    def test_success_resets_and_expired_failure_starts_new_sequence(self):
        for _ in range(4): self.attempt()
        self.assertEqual(self.attempt(PASSWORD),self.user)
        self.attempt()
        self.assertEqual(LoginGuard.objects.get(user=self.user).failures,1)
        LoginGuard.objects.filter(user=self.user).update(failures=5,locked_until=self.now-timedelta(seconds=1))
        with patch('accounts.authentication.timezone') as clock:
            clock.now.return_value=self.now
            self.attempt()
        guard=LoginGuard.objects.get(user=self.user)
        self.assertEqual(guard.failures,1);self.assertIsNone(guard.locked_until)

    def test_aliases_and_admin_username_share_counter(self):
        for _ in range(3): self.attempt(identifier=self.user.email.upper())
        self.attempt(identifier=self.user.phone)
        self.assertIsNone(authenticate(username=self.user.username,password='wrong'))
        self.assertIsNone(self.attempt(PASSWORD))
        self.assertEqual(LoginGuard.objects.get(user=self.user).failures,5)

    def test_api_and_html_login_share_generic_failure_and_csrf(self):
        client=Client(enforce_csrf_checks=True)
        token=client.get('/api/auth/csrf').json()['csrfToken']
        payload={'identifier':self.user.email,'password':'wrong'}
        self.assertEqual(client.post('/api/auth/login',payload,content_type='application/json').status_code,403)
        self.assertFalse(LoginGuard.objects.exists())
        for _ in range(4):
            response=client.post('/api/auth/login',payload,content_type='application/json',HTTP_X_CSRFTOKEN=token)
            self.assertEqual(response.status_code,401)
        self.assertEqual(client.post('/login/',{**payload,'csrfmiddlewaretoken':token}).status_code,400)
        response=client.post('/api/auth/login',{**payload,'password':PASSWORD},content_type='application/json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,401)
        self.assertEqual(response.json()['detail'],'Invalid credentials.')
        self.assertNotIn('_auth_user_id',client.session)

    def test_unknown_account_does_not_create_guard_or_leak_identifier(self):
        for _ in range(6): self.assertIsNone(self.attempt(identifier='missing@example.invalid'))
        self.assertEqual(LoginGuard.objects.count(),0)


@skipUnless(connection.vendor=='postgresql','PostgreSQL row locks required')
class LockoutRaceTests(TransactionTestCase):
    def setUp(self):
        self.user=User.objects.create_user('race',email='race@example.invalid',password=PASSWORD)

    def race(self,passwords):
        barrier=Barrier(len(passwords))
        def worker(password):
            try:
                barrier.wait(timeout=10)
                return authenticate(identifier=self.user.email,password=password) is not None
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=len(passwords)) as pool:
            return list(pool.map(worker,passwords))

    def test_simultaneous_failures_initialize_one_guard_and_lock_at_five(self):
        self.assertEqual(self.race(['wrong']*6),[False]*6)
        self.assertEqual(LoginGuard.objects.count(),1)
        guard=LoginGuard.objects.get(user=self.user)
        self.assertEqual(guard.failures,5);self.assertIsNotNone(guard.locked_until)
        self.assertIsNone(authenticate(identifier=self.user.email,password=PASSWORD))
        print('PostgreSQL login race: six failures, one guard, five counted, account locked')

    def test_correct_attempt_cannot_pass_an_existing_lock(self):
        LoginGuard.objects.create(user=self.user,failures=5,locked_until=timezone.now()+timedelta(minutes=15))
        self.assertEqual(self.race([PASSWORD,PASSWORD]),[False,False])
