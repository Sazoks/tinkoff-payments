from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TinkoffConfig(AppConfig):
    """Конфигурация приложения"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tinkoff_payments'
    verbose_name = _('Интеграция с Tinkoff Payments API')
