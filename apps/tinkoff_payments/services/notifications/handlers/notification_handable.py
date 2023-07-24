from abc import (
    ABC,
    abstractmethod,
)

from ..dto import TinkoffNotificationDTO


class NotificationHandable(ABC):
    """Интерфейс для обработчиков уведомлений"""

    @abstractmethod
    def handle(self, notification: TinkoffNotificationDTO) -> None:
        """
        Обработка уведомления.

        :param notification: DTO уведомления.
        """

        raise NotImplementedError()
