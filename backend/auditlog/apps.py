from django.apps import AppConfig


class AuditlogConfig(AppConfig):
    name='auditlog'

    def ready(self):
        from . import signals  # noqa: F401
