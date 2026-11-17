from django.conf import settings
from django.db import models
from django.db.models import Q


class LoginGuard(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='login_guard')
    failures = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(failures__lte=5), name='login_guard_failure_limit')]
