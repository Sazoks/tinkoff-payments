from utils.pipelines.exceptions import PipeProcessException

from apps.tinkoff_payments.services.payment_initialization.enums import PaymentStrategyType

from apps.notifications.services.senders.order_without_docs import OrderWithoutDocsNoticeSender

from ....models import Order
from ..dto import PipeOrderDTO
from .base import BaseOrderPipe
from ..exceptions import InvalidOrderStatusPipeException


class CheckingExistsDocumentsPipe(BaseOrderPipe):
    """
    Шаг пайплайна заказа для проверки документов на наличие.

    Пользователь может захотеть оформить заказ через менеджера.
    В таком случае, документы в запросе он не передаст.
    Менеджер обязан позвонить клиенту и вместе с ним оформить заказ.
    """

    # Чтобы выполнить операцию, заказ должен иметь один из этих статусов.
    _ALLOWED_STATUSES: list[Order.Status] = [
        Order.Status.AWAIT_PAYMENT,
        Order.Status.AWAIT_RESERVATION,
    ]

    @classmethod
    def get_pipe_name(cls) -> str:
        """Получение названия пайпа"""

        return 'Проверка наличия документов'

    def invoke(self, order_data: PipeOrderDTO) -> None:
        """
        Запуск шага пайплайна.

        :param order_data: Данные о заказе.
        """

        order = order_data.order

        if not self.is_valid_status(order.status):
            raise InvalidOrderStatusPipeException(order=order, pipe=self)

        payment_data = order_data.payment_data

        # В случае, если заказ пришел без документов, т.е. оформляется через менеджера.
        if order.with_manager:
            order.status = Order.Status.WITHOUT_DOCS
            order.save(update_fields=('status',))

            OrderWithoutDocsNoticeSender.send(order)

            raise PipeProcessException(pipe=self, message='Заказ без документов')

        if payment_data.payment_strategy == PaymentStrategyType.CARD:
            order.status = Order.Status.RESERVATION_SUCCESS
        else:
            order.status = Order.Status.PAYMENT_SUCCESS

        order.save(update_fields=('status',))

        self._result = order_data

        if self._next is not None:
            self._next.invoke(order_data)

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
