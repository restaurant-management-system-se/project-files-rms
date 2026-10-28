from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from rest_framework.authentication import SessionAuthentication
from .models import LoginGuard, User


class IdentifierBackend(ModelBackend):
    """Public login uses email/phone; keep username support for Django admin."""
    def authenticate(self, request, username=None, password=None, identifier=None, **kwargs):
        # Include Django Admin username login so it cannot bypass the guard.
        lookup = Q(username=username) if identifier is None else Q(email__iexact=identifier) | Q(phone=identifier)
        if (identifier is None and username is None) or password is None:
            return None
        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(lookup)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                User().set_password(password)
                return None
            guard, _ = LoginGuard.objects.get_or_create(user=user)
            now = timezone.now()  # Evaluate after waiting for the account lock.
            if guard.locked_until is not None and guard.locked_until > now:
                User().set_password(password)  # Same password-hash work, generic response.
                return None
            if guard.locked_until is not None:
                guard.failures, guard.locked_until = 0, None
            if user.check_password(password) and self.user_can_authenticate(user):
                guard.failures, guard.locked_until = 0, None
                guard.save(update_fields=['failures', 'locked_until'])
                return user
            guard.failures = min(guard.failures + 1, 5)
            if guard.failures == 5:
                guard.locked_until = now + timedelta(minutes=15)
            guard.save(update_fields=['failures', 'locked_until'])
        return None


class CookieSessionAuthentication(SessionAuthentication):
    def authenticate_header(self, request):
        # DRF otherwise changes unauthenticated session failures from 401 to 403.
        return 'Session realm="rms"'
