from apps.rent.tasks import order_pipeline_task
from apps.rent.services.order_pipeline.stages import OrderProcessStage
from apps.rent.services.order_pipeline.pipes import CheckingExistsDocumentsPipe

from ..dto import TinkoffNotificationDTO
from ....models import TinkoffPaymentData
from .notification_handable import NotificationHandable
from ...payment_initialization.enums import PaymentStrategyType


class TinkoffNotificationConfirmedHandler(NotificationHandable):
    """Обработчик нотификации AUTHORIZED от Тинькофф"""

    def handle(self, notification: TinkoffNotificationDTO) -> None:
        """
        Обработка нотификации.

        :param notification: DTO нотификации.
        """

        payment_data = (
            TinkoffPaymentData.objects
                .select_related('order')  # noqa: E131
                .filter(payment_id=notification.payment_id)
                .first()
        )

        # При оплаты картой при двух стадийной оплате это уведомление не придет.
        # Но если даже и придет, обрабатывать такое уведомление не нужно.
        # Мы сами подтвердим заказ в пайплайне после всех проверок.
        if payment_data is None or payment_data.payment_strategy == PaymentStrategyType.CARD:
            return

        # Отправляем заказ на обработку, если он предварительно прошел проверку.
        if CheckingExistsDocumentsPipe.is_valid_status(payment_data.order.status):
            order_pipeline_task.delay(
                payment_data.order.pk,
                OrderProcessStage.CHECKING_EXISTS_DOCUMENTS,
            )
