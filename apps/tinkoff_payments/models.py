from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .services.payment_initialization.enums import (
    PaymentStrategyType,
    ResponsePaymentInitPayloadType,
)


class TinkoffPaymentData(models.Model):
    """
    Модель для хранения информации о платеже.

    Хранит некоторую мета-информацию о платеже
    и связывает заказ с ID платежа в системе банка.
    """

    order = models.OneToOneField(
        to='rent.Order',
        on_delete=models.PROTECT,
        related_name='payment_data',
        related_query_name='payment_data',
        verbose_name=_('Order'),
    )
    payment_id = models.CharField(
        primary_key=True,
        max_length=23,
        verbose_name=_('Payment ID'),
    )
    payment_strategy = models.CharField(
        max_length=4,
        choices=PaymentStrategyType.choices(),
        verbose_name=_('Payment strategy'),
    )
    payload_type = models.CharField(
        max_length=11,
        choices=ResponsePaymentInitPayloadType.choices(),
        verbose_name=_('Payment payload type'),
    )
    payload = models.TextField(
        verbose_name=_('Payment payload'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created at'),
    )
    payment_session_lifetime = models.DurationField(
        default=settings.TINKOFF_PAYMENT_SESSION_LIFETIME,
        verbose_name=_('Payment session lifetime'),
    )

    class Meta:
        verbose_name = _('Tinkoff payment data')
        verbose_name_plural = _('Tinkoff payments data')

    @property
    def payment_session_expired_at(self) -> timezone.datetime:
        """Дата истечения платежной сессии"""

        return self.created_at + self.payment_session_lifetime

    def payment_session_is_expired(self) -> bool:
        """Проверка актуальности платежной сессии"""

        return timezone.localtime() >= self.payment_session_expired_at

    def __str__(self) -> str:
        return f'{self.payment_id}'
