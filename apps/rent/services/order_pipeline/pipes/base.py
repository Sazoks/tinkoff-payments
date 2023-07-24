from abc import (
    ABC,
    abstractmethod,
)

from utils.pipelines import PipeLike

from ..dto import PipeOrderDTO
from ....models import Order


class BaseOrderPipe(PipeLike[PipeOrderDTO], ABC):
    """Абстрактный класс шага пайплайна заказа"""

    def __init__(self) -> None:
        """Инициализатор класса"""

        self._result: PipeOrderDTO | None = None
        self._next: BaseOrderPipe | None = None

    def get_result(self) -> PipeOrderDTO | None:
        """
        Получение результата работы пайпа.

        :return: DTO с обработанными данными либо None.
        """

        return self._result

    def set_next(self, next_pipe: 'BaseOrderPipe') -> None:
        """
        Установка следующего шага после предыдущего для
        возможности асинхронного запуска.

        :param next_pipe: Следующий для выполнения шаг.
        """

        self._next = next_pipe

    @classmethod
    def get_pipe_name(cls) -> str:
        """Получение названия пайпа"""

        return cls.__name__

    @classmethod
    @abstractmethod
    def is_valid_status(cls, order_status: Order.Status) -> bool:
        """
        Проверка, что текущий статус заказа является допустимым,
        чтобы применить к заказу обработчик.

        :param order_status: Текущий статус заказа.
        """

        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_allowed_statuses(cls) -> list[Order.Status]:
        """Получение допустимых статусов для выполнения операции"""

        raise NotImplementedError()
