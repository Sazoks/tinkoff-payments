from abc import (
    ABC,
    abstractmethod,
)
from typing import Any

from apps.rent.models import Order

from ..enums import PaymentStrategyType


class InitDataBuildable(ABC):
    """Интерфейс для создания данных для запроса Init"""

    @abstractmethod
    def build(self, order: Order, payment_strategy: PaymentStrategyType) -> dict[str, Any]:
        """
        Построение тела для запроса Init.

        :param order: Объект заказа.
        :param payment_strategy: Способ оплаты.

        :return: Тело для запроса Init.
        """

        raise NotImplementedError()
