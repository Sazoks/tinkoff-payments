from apps.rent.models import Order

from ..dto import TinkoffNotificationDTO
from .notification_handable import NotificationHandable


class TinkoffNotificationDeadlineExpiredHandler(NotificationHandable):
    """Обработчик уведомления со статусом `DEADLINE_EXPIRED`"""

    def handle(self, notification: TinkoffNotificationDTO) -> None:
        """Обработка уведомления"""

        (
            Order.objects
                .select_related('payment_data')  # noqa: E131
                .filter(payment_data__pk=notification.payment_id)
                .update(status=Order.Status.PAYMENT_SESSION_EXPIRED)
        )
