from typing import Type

from apps.notifications.services.senders.abstract import NoticeSender
from apps.notifications.services.senders import OrderCanceledNoticeSender

from apps.tinkoff_payments.services.payment_cancellation_service import (
    TinkoffPaymentCancellationService,
)

from ....models import Order
from ..dto import PipeOrderDTO
from .base import BaseOrderPipe
from ..exceptions import InvalidOrderStatusPipeException


class CancelOrderPipe(BaseOrderPipe):
    """
    Шаг пайплайна для отмены заказа.

    Не участвует при сборке основного пайплайна в билдере.
    """

    # Чтобы выполнить операцию, заказ должен иметь один из этих статусов.
    _ALLOWED_STATUSES: list[Order.Status] = [
        Order.Status.NEW,
        Order.Status.AWAIT_PAYMENT,
        Order.Status.AWAIT_RESERVATION,
        Order.Status.RESERVATION_SUCCESS,
        Order.Status.PAYMENT_SUCCESS,
        Order.Status.WITHOUT_DOCS,
        Order.Status.VERIFY_FAILED,
        Order.Status.APPROVAL_SUCCESS,
        Order.Status.CONFIRM_PAYMENT_FAILED,
        Order.Status.BOOKED,
    ]
    default_notice_sender_class: Type[NoticeSender] = OrderCanceledNoticeSender

    def __init__(self, notice_sender: NoticeSender | None = None) -> None:
        """
        Инициализатор класса.

        :param notice_sender:
            Отправщик уведомления после отмены заказа.
            По-умолчанию используется `OrderCanceledNoticeSender`.
        """

        super().__init__()

        self.__notice_sender = notice_sender or self.default_notice_sender_class()

    def invoke(self, order_data: PipeOrderDTO) -> None:
        """
        Запуск шага пайплайна.

        Отменяем платеж у заказа, переводим в статус `CANCELED` и отправляем
        уведомления об отмене.

        :param order_data: Данные о заказе.
        """

        order = order_data.order

        if not self.is_valid_status(order.status):
            raise InvalidOrderStatusPipeException(order=order, pipe=self)

        payment_data = order_data.payment_data

        TinkoffPaymentCancellationService(payment_data.payment_id).cancel()

        order.status = Order.Status.CANCELED
        order.save(update_fields=('status',))

        self._result = order_data

        self.__notice_sender.send(order)

    @classmethod
    def get_pipe_name(cls) -> str:
        """Получение названия пайпа"""

        return 'Отмена заказа'

    @classmethod
    def is_valid_status(cls, order_status: Order.Status) -> bool:
        """
        Проверка, что текущий статус заказа является допустимым,
        чтобы применить к заказу обработчик.

        :param order_status: Текущий статус заказа.
        """

        return order_status in cls._ALLOWED_STATUSES

    @classmethod
    def get_allowed_statuses(cls) -> list[Order.Status]:
        """Получение допустимых статусов для выполнения операции"""

        return cls._ALLOWED_STATUSES
