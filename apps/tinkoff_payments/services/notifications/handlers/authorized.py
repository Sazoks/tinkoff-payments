from apps.rent.tasks import order_pipeline_task
from apps.rent.services.order_pipeline.stages import OrderProcessStage
from apps.rent.services.order_pipeline.pipes import CheckingExistsDocumentsPipe

from ..dto import TinkoffNotificationDTO
from ....models import TinkoffPaymentData
from .notification_handable import NotificationHandable
from ...payment_initialization.enums import PaymentStrategyType


class TinkoffNotificationAuthorizedHandler(NotificationHandable):
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

        # Для заказов со способом оплаты через СБП обрабатывать AUTHORIZED не нужно.
        if payment_data is None or payment_data.payment_strategy == PaymentStrategyType.SBP:
            return

        # Отправляем заказ на обработку, если он предварительно прошел проверку.
        if CheckingExistsDocumentsPipe.is_valid_status(payment_data.order.status):
            order_pipeline_task.delay(
                payment_data.order.pk,
                OrderProcessStage.CHECKING_EXISTS_DOCUMENTS,
            )
