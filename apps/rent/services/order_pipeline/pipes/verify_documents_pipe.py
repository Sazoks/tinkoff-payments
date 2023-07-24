from apps.users.models.client_profile import ClientProfile
from apps.users.services.documents_verification import ClientDocumentsVerificationService

from utils.pipelines.exceptions import PipeProcessException

from apps.notifications.services.senders.documents_verify_failed import (
    DocumentsVerifyFailedNoticeSender,
)

from ..dto import PipeOrderDTO
from ....models import Order
from .base import BaseOrderPipe
from ..exceptions import InvalidOrderStatusPipeException


class VerifyDocumentsPipe(BaseOrderPipe):
    """Шаг пайплайна заказа для проверки документов"""

    # Чтобы выполнить операцию, заказ должен иметь один из этих статусов.
    _ALLOWED_STATUSES: list[Order.Status] = [
        Order.Status.PAYMENT_SUCCESS,
        Order.Status.RESERVATION_SUCCESS,
        Order.Status.WITHOUT_DOCS,
        Order.Status.VERIFY_FAILED,
    ]

    @classmethod
    def get_pipe_name(cls) -> str:
        """Получение названия пайпа"""

        return 'Проверка документов'

    def invoke(self, order_data: PipeOrderDTO) -> None:
        """
        Запуск шага пайплайна.

        :param order_data: Данные о заказе.
        """

        order = order_data.order

        if not self.is_valid_status(order.status):
            raise InvalidOrderStatusPipeException(order=order, pipe=self)

        order.status = Order.Status.ON_APPROVAL
        order.save(update_fields=('status',))

        client: ClientProfile = order.user.client_profile

        # Запуск проверки документов.
        try:
            service = ClientDocumentsVerificationService()
            service.verify(client)
        except Exception as e:
            self.__handle_verify_failed(order_data)

            raise PipeProcessException(
                pipe=self,
                message='Непредвиденная ошибка во время проверки документов',
            ) from e

        if not client.is_full_verified_profile:
            self.__handle_verify_failed(order_data)

            raise PipeProcessException(pipe=self, message='Документы не прошли проверку')

        order.status = Order.Status.APPROVAL_SUCCESS
        order.save(update_fields=('status',))

        self._result = order_data

        if self._next is not None:
            self._next.invoke(order_data)

    @classmethod
    def is_valid_status(cls, order_status: Order.Status) -> bool:
        """
        Проверка, что текущий статус заказа является допустимым,
        чтобы применить к заказу обработчик.

        :param order_status: Текущий статус заказа.
        """

        return order_status in cls._ALLOWED_STATUSES

    @classmethod
    def get_allowed_statuses(cls) -> list[Order.Status]:
        """Получение допустимых статусов для выполнения операции"""

        return cls._ALLOWED_STATUSES

    @staticmethod
    def __handle_verify_failed(order_data: PipeOrderDTO) -> None:
        """Обработка заказа в случае неудачной проверки документов"""

        order_data.order.status = Order.Status.VERIFY_FAILED
        order_data.order.save(update_fields=('status',))

        # Отправка уведомлений менеджерам и клиенту о неудачной проверке.
        DocumentsVerifyFailedNoticeSender.send(order_data.order)
