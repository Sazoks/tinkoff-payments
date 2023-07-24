from ..enums import NotificationPaymentStatus
from .notification_handable import NotificationHandable
from .rejected import TinkoffNotificationRejectedHandler
from .confirmed import TinkoffNotificationConfirmedHandler
from .authorized import TinkoffNotificationAuthorizedHandler
from .deadline_expired import TinkoffNotificationDeadlineExpiredHandler


class TinkoffNotificationHandlerFactory:
    """
    Фабрика создания обработчиков нотификаций в зависимости
    от статуса платежа и стратегии оплаты.

    Нотификации Тинькофф (со слов тех. поддержки), служат лишь
    для удобства. Статусы `AUTHORIZED`, `CONFIRMED` и `REJECTED`
    мы можем получить только от банка, но остальные статусы
    (`CANCELED`, `REFUNDED` и др.) мы можем получить в ответе
    на запрос от сервера. Поэтому их не нужно обрабатывать в
    нотификациях.
    """

    _NOTIFICATION_HANDLER_CLASSES_MAP = {
        NotificationPaymentStatus.AUTHORIZED: TinkoffNotificationAuthorizedHandler,
        NotificationPaymentStatus.CONFIRMED: TinkoffNotificationConfirmedHandler,
        NotificationPaymentStatus.REJECTED: TinkoffNotificationRejectedHandler,
        NotificationPaymentStatus.DEADLINE_EXPIRED: TinkoffNotificationDeadlineExpiredHandler,
    }

    @classmethod
    def create(
        cls,
        payment_status: NotificationPaymentStatus,
    ) -> NotificationHandable | None:
        """
        Создание обработчика нотификации.

        :param payment_status: Статус платежа из нотификации.
        """

        handler_class = cls._NOTIFICATION_HANDLER_CLASSES_MAP.get(payment_status)
        if handler_class is not None:
            return handler_class()
