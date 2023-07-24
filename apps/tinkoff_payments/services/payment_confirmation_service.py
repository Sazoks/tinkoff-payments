from requests import Response

from constance import config
from rest_framework import status

from .core.endpoints import TinkoffRoutes
from .core.api_client import TinkoffPaymentsClient
from .core.exceptions import TinkoffResponseException


class TinkoffPaymentConfirmationService:
    """Сервис для подтверждения платежа"""

    def __init__(self, payment_id: str) -> None:
        """Инициализатор класса"""

        self.__api_client = TinkoffPaymentsClient(
            base_url=config.TINKOFF_API_URL,
            terminal_key=config.TINKOFF_TERMINAL_KEY,
            password=config.TINKOFF_PASSWORD,
        )
        self.__payment_id = payment_id

    def confirm(self) -> Response:
        """Подтвреждение платежа"""

        response = self.__api_client.request(
            method='post',
            url_postfix=TinkoffRoutes.CONFIRM,
            data={'PaymentId': self.__payment_id},
        )
        if response.status_code != status.HTTP_200_OK or not response.json()['Success']:
            raise TinkoffResponseException(response)

        return response
