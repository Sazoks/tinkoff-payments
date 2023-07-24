from typing import (
    Any,
    Final,
)

from constance import config
from django.conf import settings
from django.utils import timezone

from apps.rent.models import Order

from ..enums import (
    Tax,
    PayType,
    Taxation,
    PaymentMethod,
    PaymentObject,
    PaymentStrategyType,
)
from .init_data_buildable import InitDataBuildable


class AdvancePaymentDataBuilder(InitDataBuildable):
    """Класс для построения данных аванса для запроса Init"""

    _PAYMENT_TYPE_MAP: Final[dict[PaymentStrategyType, PayType]] = {
        PaymentStrategyType.CARD: PayType.TWO_STAGE,
        PaymentStrategyType.SBP: PayType.SINGLE_STAGE,
    }

    def build(self, order: Order, payment_strategy: PaymentStrategyType) -> dict[str, Any]:
        """
        Построение тела для запроса Init.

        :param order: Объект заказа.
        :param payment_strategy: Способ оплаты.

        :return: Тело для запроса Init.
        """

        # Получим дату истечения платежной ссылки без микросекунд в ISO-формате.
        # Тинькофф не принимает даты с микросекундами.
        now = timezone.localtime()
        now_without_microseconds = timezone.datetime(
            year=now.year, month=now.month,
            day=now.day, hour=now.hour, minute=now.minute,
            second=now.second, tzinfo=now.tzinfo,
        )
        datetime_expired_iso = (
            now_without_microseconds + settings.TINKOFF_PAYMENT_SESSION_LIFETIME
        ).isoformat()

        return {
            'Amount': config.TINKOFF_ADVANCE_AMOUNT,
            'OrderId': str(order.pk),
            'NotificationURL': settings.TINKOFF_NOTIFICATIONS_URL,
            'PayType': self._PAYMENT_TYPE_MAP[payment_strategy].value,
            'RedirectDueDate': datetime_expired_iso,
            'SuccessURL': (
                f'{settings.FRONTEND_HOST}/orders/{order.pk}'
                '?Success=${Success}&ErrorCode=${ErrorCode}&Message=${Message}'
                '&Details=${Details}&Amount=${Amount}&MerchantEmail=${MerchantEmail}'
                '&MerchantName=${MerchantName}&OrderId=${OrderId}&PaymentId=${PaymentId}'
                '&TranDate=${TranDate}&BackUrl=${BackUrl}&CompanyName=${CompanyName}'
                '&EmailReq=${EmailReq}&PhonesReq=${PhonesReq}'
            ),
            'FailURL': (
                f'{settings.FRONTEND_HOST}/orders/{order.pk}'
                '?Success=${Success}&ErrorCode=${ErrorCode}&Message=${Message}'
                '&Details=${Details}&Amount=${Amount}&MerchantEmail=${MerchantEmail}'
                '&MerchantName=${MerchantName}&OrderId=${OrderId}&PaymentId=${PaymentId}'
                '&TranDate=${TranDate}&BackUrl=${BackUrl}&CompanyName=${CompanyName}'
                '&EmailReq=${EmailReq}&PhonesReq=${PhonesReq}'
            ),
            'Receipt': {
                'Phone': str(order.user.phone),
                'Taxation': Taxation.USN_INCOME_OUTCOME.value,
                'Items': [
                    {
                        'Name': str(order),
                        'Quantity': 1,
                        'Amount': config.TINKOFF_ADVANCE_AMOUNT,
                        'Price': config.TINKOFF_ADVANCE_AMOUNT,
                        'PaymentMethod': PaymentMethod.PREPAYMENT.value,
                        'PaymentObject': PaymentObject.SERVICE.value,
                        'Tax': Tax.NONE.value,
                    }
                ],
            },
        }
