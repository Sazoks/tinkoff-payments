from abc import (
    ABC,
    abstractmethod,
)
from typing import Any
from requests import Response

from ..dto import ResponsePaymentInitDTO


class PaymentInitializable(ABC):
    """
    Интерфейс для объектов, способных инициализировать
    платежную сессию.
    """

    @abstractmethod
    def init(self, data: dict[str, Any]) -> Response:
        """
        Инициализаци платежной сессии.

        :param data:
            Данные для инициализации платежа.
            Содержат данные о заказе и другую информацию.

        :return: Объект ответа.
        """

        raise NotImplementedError()

    @abstractmethod
    def get_data_from_response(self, response: Response) -> ResponsePaymentInitDTO:
        """
        Получение нужных данных из объекта ответа.

        У каждого имплементирующего данный интерфейс класса
        значение будет под своим ключом.

        :param response: Объект ответа.

        :return: Объет с данными после инициализации платежа.
        """

        raise NotImplementedError()
