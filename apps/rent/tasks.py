import logging
import traceback

from celery import shared_task
from django.utils import timezone

from .models.order import Order
from .services.order_pipeline.dto import PipeOrderDTO
from .services.order_pipeline.stages import OrderProcessStage
from .services.order_pipeline.builder import OrderPipelineBuilder


logger = logging.getLogger(__name__)


@shared_task
def order_pipeline_task(order_id: int, start_pipeline_step: OrderProcessStage) -> None:
    """
    Задача на обработку заказа по пайплайну после инициализации платежа.

    :param order_id: ID заказа с инициализированной платежной сессией в системе.
    :param start_pipeline_step: Шаг, с которого нужно сбилдить пайплайн.
    """

    order = (
        Order.objects
            .select_related('payment_data', 'user__client_profile')  # noqa: E131
            .filter(pk=order_id)  # noqa: E131
            .first()  # noqa: E131
    )
    payment_data = order.payment_data

    order_pipeline = OrderPipelineBuilder(start_pipeline_step).build()
    try:
        order_pipeline.invoke(PipeOrderDTO(order, payment_data))
    except Exception:
        logger.error(
            f'Ошибка обработки заказа №{order_id}\n'
            f'Причина: {traceback.format_exc()}'
        )


@shared_task
def order_booked_to_active_task() -> None:
    """
    Задача для перевода заказов со статусом `BOOKED` в `ACTIVE`.

    Переводит заказ в статус `ACTIVE`, когда наступает время проката.
    """

    Order.objects.filter(
        status=Order.Status.BOOKED,
        starts_at__lte=timezone.localtime(),
    ).update(status=Order.Status.ACTIVE)
