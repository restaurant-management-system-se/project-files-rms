from time import time
from django.conf import settings
from django.contrib.auth import logout


class IdleSessionMiddleware:
    """Server-side idle deadline shared by API, pages and Django admin."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = time()
            last = request.session.get("last_activity", now)
            if now - last >= settings.SESSION_IDLE_TIMEOUT:
                logout(request)
                request.session_expired = True
            elif request.path != "/api/auth/session" or "last_activity" not in request.session:
                # Status checks/polling (including a future Node verifier) are not activity.
                request.session["last_activity"] = now
                request.session.set_expiry(settings.SESSION_IDLE_TIMEOUT)
        return self.get_response(request)
