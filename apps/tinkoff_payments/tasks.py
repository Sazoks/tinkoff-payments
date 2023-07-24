import logging

from celery import shared_task
from django.db.models import (
    F,
    DateTimeField,
    ExpressionWrapper,
)
from django.utils import timezone

from apps.rent.models.order import Order


logger = logging.getLogger(__name__)


@shared_task
def handle_expired_payment_sessions_task() -> None:
    """
    Задача на обработку заказов с истекшей платежной сессией.

    Переводит такие заказы в статус `PAYMENT_SESSION_EXPIRED`.

    Согласно информации от тех. поддержке Тинькофф, такие заказы
    нет нужды отменять с нашей стороны, т.к. никаких средств
    еще не было зерезервированно/оплачено.
    """

    logger.info('Старт проверки истекших заказов')

    expired_orders_count = (
        Order.objects
            .select_related('payment_data')  # noqa: E131
            .filter(
                status__in=(
                    Order.Status.AWAIT_PAYMENT,
                    Order.Status.AWAIT_RESERVATION,
                ),
            )
            .annotate(  # noqa: E131
                expired_at=ExpressionWrapper(
                    expression=F('payment_data__created_at')
                    + F('payment_data__payment_session_lifetime'),
                    output_field=DateTimeField(),
                )
            )
            .filter(expired_at__lte=timezone.localtime())  # noqa: E131
            .update(status=Order.Status.PAYMENT_SESSION_EXPIRED)  # noqa: E131
    )

    logger.info(f'Кол-во обнаруженных истекших заказов: {expired_orders_count}')
