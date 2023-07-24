from datetime import timedelta
from dataclasses import dataclass

from .enums import (
    PaymentStrategyType,
    ResponsePaymentInitPayloadType,
)


@dataclass
class ResponsePaymentInitDTO:
    """
    Дата-класс для данных из ответа после
    инициализации платежа.

    :param order_id: ID заказа в нашей системе.
    :param payment_id: ID платежа в системе банка.
    :param payment_strategy: Способ платежа.
    :param payload_type: Тип полезной нагрузки для оплаты.
    :param payload:
        Сама полезная нагрузка для оплаты.
        Это может быть либо URL на платежную форму,
        либо URL QR-кода, либо SVG QR-кода.
    """

    order_id: int
    payment_id: str
    payment_strategy: PaymentStrategyType
    payload_type: ResponsePaymentInitPayloadType
    payload: str
    payment_session_lifetime: timedelta
