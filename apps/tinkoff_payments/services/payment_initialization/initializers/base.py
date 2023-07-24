from typing import Any
from requests import Response

from django.conf import settings

from utils.api_tools.http_statuses import HTTPStatus

from ..enums import (
    PaymentStrategyType,
    ResponsePaymentInitPayloadType,
)
from ..dto import ResponsePaymentInitDTO
from ...core.endpoints import TinkoffRoutes
from ...core.api_client import TinkoffPaymentsClient
from ...core.exceptions import TinkoffResponseException
from .payment_initializable import PaymentInitializable


class TinkoffPaymentInitializer(PaymentInitializable):
    """Класс для инициализации платежа в Тинькофф"""

    def __init__(self, api_client: TinkoffPaymentsClient) -> None:
        """
        Инициализатор класса.

        :param api_client: Объект для работы с API Тинькофф.
        """

        self.__api_client = api_client

    def init(self, data: dict[str, Any]) -> Response:
        """
        Инициализация платежной сессии.

        :param data:
            Данные для инициализации платежа.
            Содержат данные о заказе и другую информацию.

        :return: Объект ответа с ссылкой на платежную форму.
        """

        response = self.__api_client.request(
            method='post',
            url_postfix=TinkoffRoutes.INIT,
            data=data,
        )
        if response.status_code != HTTPStatus.HTTP_200_OK or not response.json()['Success']:
            raise TinkoffResponseException(response)

        return response

    def get_data_from_response(self, response: Response) -> ResponsePaymentInitDTO:
        """
        Получение нужных данных из объекта ответа.

        :param response: Объект ответа.

        :return: Объет с данными после инициализации платежа.
        """

        response_json: dict[str, Any] = response.json()

        return ResponsePaymentInitDTO(
            order_id=int(response_json['OrderId']),
            payment_id=response_json['PaymentId'],
            payment_strategy=PaymentStrategyType.CARD,
            payload_type=ResponsePaymentInitPayloadType.PAYMENT_URL,
            payload=response_json['PaymentURL'],
            payment_session_lifetime=settings.TINKOFF_PAYMENT_SESSION_LIFETIME,
        )
