from ...models import Order
from .pipes.base import BaseOrderPipe


class InvalidOrderStatusPipeException(Exception):
    """
    Исключение неверного статуса заказа при
    выполнении какой-либо операции.
    """

    def __init__(
        self,
        order: Order,
        pipe: BaseOrderPipe,
        *args, **kwargs,
    ) -> None:
        """Инициализатор класса"""

        self.order = order
        self.pipe = pipe
        self.message = self.get_template_error_message().format(
            order_id=order.pk,
            order_status=order.status,
            allowed_statuses=pipe.get_allowed_statuses(),
        )

        super().__init__(self.message)

    @staticmethod
    def get_template_error_message() -> str:
        """Получение шаблона сообщения об ошибке"""

        return (
            'Неверный статус заказа №{order_id}\n'
            'Текущий статус: {order_status}\n'
            'Допустимые статусы: {allowed_statuses}'
        )


class NoResultOrderPipeException(Exception):
    """
    Исключение, когда не удалось получить результат
    работы пайпа.
    """

    def __init__(self, pipe: BaseOrderPipe, *args, **kwargs) -> None:
        """Инициализатор класса"""

        self.pipe = pipe
        self.message = self.get_template_error_message().format(
            pipe_name=pipe.get_pipe_name(),
        )

        super().__init__(self.message)

    @staticmethod
    def get_template_error_message() -> str:
        """Получение шаблона сообщения об ошибке"""

        return (
            'Ошибка получения результата этапа пайплайна\n'
            'Этап обработки: {pipe_name}\n'
        )
