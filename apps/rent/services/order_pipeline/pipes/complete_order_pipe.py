from ..dto import PipeOrderDTO
from ....models import Order
from .base import BaseOrderPipe
from ..exceptions import InvalidOrderStatusPipeException


class CompleteOrderPipe(BaseOrderPipe):
    """
    Шаг пайплайна для завершения заказа.

    Не участвует при сборке основного пайплайна в билдере.
    Используется отдельно в API завершения заказа.
    """

    # Чтобы выполнить операцию, заказ должен иметь один из этих статусов.
    _ALLOWED_STATUSES: list[Order.Status] = [
        Order.Status.ACTIVE,
    ]

    @classmethod
    def get_pipe_name(cls) -> str:
        """Получение названия пайпа"""

        return 'Завершение заказа'

    def invoke(self, order_data: PipeOrderDTO) -> None:
        """
        Запуск шага пайплайна.

        :param order_data: Данные о заказе.
        """

        order = order_data.order

        if not self.is_valid_status(order.status):
            raise InvalidOrderStatusPipeException(order=order, pipe=self)

        order.status = Order.Status.COMPLETED
        order.save(update_fields=('status',))

        self._result = order_data

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
