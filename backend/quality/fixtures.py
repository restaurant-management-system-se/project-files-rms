"""Isolated role fixtures, real cookie/CSRF client and reversible clock."""
from contextlib import contextmanager
from unittest.mock import patch
from django.test import Client
from accounts.models import User


def role_users(password='Harness#72'):
    """Call only within a TestCase database; do not enable reserved demo users."""
    users = {}
    for role in User.Role:
        user = User(username=f'fixture_{role.lower()}', email=f'{role.lower()}@example.invalid', role=role)
        user.set_password(password)
        user.save()
        users[role] = user
    return users


class SessionClient(Client):
    def __init__(self, *args, **kwargs):
        kwargs['enforce_csrf_checks'] = True
        super().__init__(*args, **kwargs)

    def csrf(self):
        return self.get('/api/auth/csrf').json()['csrfToken']

    def json_write(self, method, path, payload):
        return getattr(self, method.lower())(path, payload, content_type='application/json',
                                            HTTP_X_CSRFTOKEN=self.csrf())


@contextmanager
def auth_clock(epoch):
    """Patch the existing auth seams, restoring both automatically after use."""
    with patch('accounts.views.time', return_value=epoch), patch('accounts.middleware.time', return_value=epoch):
        yield
