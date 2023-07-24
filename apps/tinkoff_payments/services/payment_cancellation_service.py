from requests import Response

from constance import config
from rest_framework import status

from .core.endpoints import TinkoffRoutes
from .core.api_client import TinkoffPaymentsClient
from .core.exceptions import TinkoffResponseException


class TinkoffPaymentCancellationService:
    """Сервис для полной отмены платежной сессии у заказа"""

    def __init__(self, payment_id: str) -> None:
        """Инициализатор класса"""

        self.__api_client = TinkoffPaymentsClient(
            base_url=config.TINKOFF_API_URL,
            terminal_key=config.TINKOFF_TERMINAL_KEY,
            password=config.TINKOFF_PASSWORD,
        )
        self.__payment_id = payment_id

    def cancel(self) -> Response:
        """Отмена платежной сессии"""

        response = self.__api_client.request(
            method='post',
            url_postfix=TinkoffRoutes.CANCEL,
            data={'PaymentId': self.__payment_id},
        )
        if response.status_code != status.HTTP_200_OK or not response.json()['Success']:
            raise TinkoffResponseException(response)

        return response
