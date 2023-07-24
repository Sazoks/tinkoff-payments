from dataclasses import dataclass

from apps.tinkoff_payments.models import TinkoffPaymentData

from ...models import Order


@dataclass
class PipeOrderDTO:
    """DTO с данными заказа и платежа для пайплайна"""

    order: Order
    payment_data: TinkoffPaymentData | None = None
