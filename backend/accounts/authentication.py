from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework.authentication import SessionAuthentication
from .models import User


class IdentifierBackend(ModelBackend):
    """Public login uses email/phone; keep username support for Django admin."""
    def authenticate(self, request, username=None, password=None, identifier=None, **kwargs):
        if identifier is None:
            return super().authenticate(request, username=username, password=password, **kwargs)
        try:
            user = User.objects.get(Q(email__iexact=identifier) | Q(phone=identifier))
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            User().set_password(password)  # Keep missing-account password hashing work.
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


class CookieSessionAuthentication(SessionAuthentication):
    def authenticate_header(self, request):
        # DRF otherwise changes unauthenticated session failures from 401 to 403.
        return 'Session realm="rms"'
