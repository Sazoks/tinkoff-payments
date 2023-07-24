from apps.rent.models import Order

from ..dto import TinkoffNotificationDTO
from .notification_handable import NotificationHandable


class TinkoffNotificationRejectedHandler(NotificationHandable):
    """Обработчик нотификации REJECTED от Тинькофф"""

    def handle(self, notification: TinkoffNotificationDTO) -> None:
        """
        Обработка нотификации.

        :param notification: DTO нотификации.
        """

        order = Order.objects.filter(pk=notification.order_id).first()
        if order is None:
            return

        order.status = Order.Status.REJECTED
        order.save(update_fields=('status',))
