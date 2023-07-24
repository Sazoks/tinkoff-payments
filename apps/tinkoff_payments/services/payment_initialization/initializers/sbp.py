from typing import (
    Any,
    Final,
)
from requests import Response

from django.conf import settings

from utils.api_tools.http_statuses import HTTPStatus

from ..enums import (
    QrDataType,
    PaymentStrategyType,
    ResponsePaymentInitPayloadType,
)
from ..dto import ResponsePaymentInitDTO
from ...core.endpoints import TinkoffRoutes
from ...core.api_client import TinkoffPaymentsClient
from ...core.exceptions import TinkoffResponseException
from .payment_initializable import PaymentInitializable


class TinkoffSBPInitializer(PaymentInitializable):
    """Класс для инициализации платежа через СБП"""

    _QR_RETURNING_PARAM_MAP: Final[dict[QrDataType, ResponsePaymentInitPayloadType]] = {
        QrDataType.IMAGE: ResponsePaymentInitPayloadType.QR_IMAGE,
        QrDataType.PAYLOAD: ResponsePaymentInitPayloadType.QR_URL,
    }

    def __init__(self, api_client: TinkoffPaymentsClient, qr_data_type: QrDataType) -> None:
        """
        Инициализатор класса.

        :param api_client: Объект для работы с API Тинькофф.
        :param qr_data_type:
            Тип возвращаемого значения: либо ссылка на QR-код,
            либо SVG-изображение.
        """

        self.__api_client = api_client
        self.__qr_data_type = qr_data_type

    @property
    def qr_data_type(self) -> QrDataType:
        """Геттер типа возвращаемого QR-кода"""

        return self.__qr_data_type

    @qr_data_type.setter
    def qr_data_type(self, new_type: QrDataType) -> None:
        """Сеттер типа возвращаемого QR-кода"""

        if not isinstance(new_type, QrDataType):
            raise ValueError(f'Такого формата QR-кода не существует: {new_type}')

        self.__qr_data_type = new_type

    def init(self, data: dict[str, Any]) -> Response:
        """
        Инициализаци платежной сессии через СБП.

        :param data:
            Данные для инициализации платежа.
            Содержат данные о заказе и другую информацию.

        :return:
            Объект ответа от Тинькофф, содержащий либо URL-адрес
            QR-кода, либо SVG-изображение с QR-кодом..
        """

        response = self.__api_client.request(
            method='post',
            url_postfix=TinkoffRoutes.INIT,
            data=data,
        )
        self._check_response(response)

        payment_id: str = response.json()['PaymentId']

        response = self.__api_client.request(
            method='post',
            url_postfix=TinkoffRoutes.GET_QR,
            data={
                'PaymentId': payment_id,
                'DataType': self.qr_data_type.value,
            },
        )
        self._check_response(response)

        return response

    @staticmethod
    def _check_response(response: Response) -> None:
        """Проверка корректности ответа"""

        if response.status_code != HTTPStatus.HTTP_200_OK or not response.json()['Success']:
            raise TinkoffResponseException(response)

    def get_data_from_response(self, response: Response) -> ResponsePaymentInitDTO:
        """
        Получение нужных данных из объекта ответа.

        :param response: Объект ответа.

        :return: Объект ответа с ссылкой на платежную форму.
        """

        response_json: dict[str, Any] = response.json()

        return ResponsePaymentInitDTO(
            order_id=int(response_json['OrderId']),
            payment_id=response_json['PaymentId'],
            payment_strategy=PaymentStrategyType.SBP,
            payload_type=self._QR_RETURNING_PARAM_MAP[self.__qr_data_type],
            payload=response_json['Data'],
            payment_session_lifetime=settings.TINKOFF_PAYMENT_SESSION_LIFETIME,
        )
