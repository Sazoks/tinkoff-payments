from dataclasses import dataclass

from .enums import NotificationPaymentStatus


@dataclass
class TinkoffNotificationDTO:
    """
    DTO для уведомления о статусе платежа от Тинькофф.
    """

    terminal_key: str
    token: str
    order_id: int
    success: bool
    status: NotificationPaymentStatus
    payment_id: str
    error_code: str
    amount: int
