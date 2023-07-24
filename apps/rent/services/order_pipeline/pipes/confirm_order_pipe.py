from utils.pipelines.exceptions import PipeProcessException

from apps.tinkoff_payments.services.payment_confirmation_service import (
    TinkoffPaymentConfirmationService,
)
from apps.tinkoff_payments.services.payment_initialization.enums import PaymentStrategyType

from apps.notifications.services.senders.order_confirmed import OrderConfirmedNoticeSender

from ..dto import PipeOrderDTO
from ....models import Order
from .base import BaseOrderPipe
from ..exceptions import InvalidOrderStatusPipeException


class ConfirmOrderPipe(BaseOrderPipe):
    """Шаг пайплайна заказа для подтверждения заказа"""

    # Чтобы выполнить операцию, заказ должен иметь один из этих статусов.
    _ALLOWED_STATUSES: list[Order.Status] = [
        Order.Status.APPROVAL_SUCCESS,
        Order.Status.WITHOUT_DOCS,
        Order.Status.VERIFY_FAILED,
        Order.Status.CONFIRM_PAYMENT_FAILED,
    ]

    @classmethod
    def get_pipe_name(cls) -> str:
        """Получение названия пайпа"""

        return 'Подтверждение заказа'

    def invoke(self, order_data: PipeOrderDTO) -> None:
        """
        Запуск шага пайплайна.

        :param order_data: Данные о заказе.
        """

        order = order_data.order

        if not self.is_valid_status(order.status):
            raise InvalidOrderStatusPipeException(order=order, pipe=self)

        payment_data = order_data.payment_data

        # Для платежей через карту используется двух стадийная оплата
        # для резервации суммы. Поэтому необходимо вручную подтвердить платеж.
        if payment_data.payment_strategy == PaymentStrategyType.CARD:
            self.__manual_confirm_payment(order_data)

        order.status = Order.Status.BOOKED
        order.save(update_fields=('status',))

        self._result = order_data

        OrderConfirmedNoticeSender.send(order)

        if self._next is not None:
            self._next.invoke(order_data)

    def __manual_confirm_payment(self, order_data: PipeOrderDTO) -> None:
        """
        Ручное подтверждение платежа.

        :param order_data: DTO с данными о заказе.
        """

        order = order_data.order
        payment_data = order_data.payment_data

        order.status = Order.Status.AWAIT_CONFIRM_PAYMENT
        order.save(update_fields=('status',))

        try:
            TinkoffPaymentConfirmationService(payment_data.payment_id).confirm()
        except Exception as e:
            order.status = Order.Status.CONFIRM_PAYMENT_FAILED
            order.save(update_fields=('status',))

            raise PipeProcessException(
                pipe=self,
                message='Ошибка подтверждения платежа',
            ) from e

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
