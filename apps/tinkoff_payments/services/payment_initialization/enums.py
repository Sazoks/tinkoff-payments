"""
Здесь содержатся все возможные значения для инициализации платежа.
"""

from enum import (
    auto,
    Enum,
)
from typing import (
    Any,
    Iterable,
)


class PaymentStrategyType(str, Enum):
    """Стратегии оплаты"""

    def _generate_next_value_(
        name: str, start: int,  # noqa: N805
        count: int, last_values: list[str],
    ) -> str:
        return name.lower()

    CARD = auto()
    SBP = auto()

    @classmethod
    def choices(cls) -> Iterable[tuple[str, Any]]:
        return tuple((i.value, i.name) for i in cls)


class ResponsePaymentInitPayloadType(str, Enum):
    """
    После процесса инициализации мы можем произвести оплату
    одним из нижеперечисленных способов.
    Эти значения отправятся на клиент.
    """

    def _generate_next_value_(
        name: str, start: int,  # noqa: N805
        count: int, last_values: list[str],
    ) -> str:
        return name.lower()

    PAYMENT_URL = auto()
    QR_URL = auto()
    QR_IMAGE = auto()

    @classmethod
    def choices(cls) -> Iterable[tuple[str, Any]]:
        return tuple((i.value, i.name) for i in cls)


class QrDataType(str, Enum):
    """
    При инциализации через СБП у нас есть два варианта,
    какого типа мы хотим получить QR-код: изображением или ссылкой.
    Используются при формировании запроса GetQr.
    """

    IMAGE = 'IMAGE'
    PAYLOAD = 'PAYLOAD'


class PayType(str, Enum):
    """Типы платежей"""

    SINGLE_STAGE = 'O'
    TWO_STAGE = 'T'


class Taxation(str, Enum):
    """Системы налогообложения"""

    OSN = 'osn'
    USN_INCOME = 'usn_income'
    USN_INCOME_OUTCOME = 'usn_income_outcome'
    PATENT = 'patent'
    ENVD = 'envd'
    ESN = 'esn'


class Tax(str, Enum):
    """Ставки НДС"""

    NONE = 'none'
    VAT_0 = 'vat0'
    VAT_10 = 'vat10'
    VAT_20 = 'vat20'
    VAT_110 = 'vat110'
    VAT_120 = 'vat120'


class PaymentMethod(str, Enum):
    """Способ расчета"""

    FULL_PAYMENT = 'full_payment'
    FULL_PREPAYMENT = 'full_prepayment'
    PREPAYMENT = 'prepayment'
    ADVANCE = 'advance'
    PARTIAL_PAYMENT = 'partial_payment'
    CREDIT = 'credit'
    CREDIT_PAYMENT = 'credit_payment'


class PaymentObject(str, Enum):
    """Предмет расчета"""

    COMMODITY = 'commodity'
    EXCISE = 'excise'
    JOB = 'job'
    SERVICE = 'service'
    GAMBLING_BET = 'gambling_bet'
    GAMBLING_PRIZE = 'gambling_prize'
    LOTTERY = 'lottery'
    LOTTERY_PRIZE = 'lottery_prize'
    INTELLECTUAL_ACTIVITY = 'intellectual_activity'
    PAYMENT = 'payment'
    AGENT_COMMISSION = 'agent_commission'
    COMPOSITE = 'composite'
    ANOTHER = 'another'
