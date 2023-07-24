from constance import config
from django.db import transaction

from ....models import Order
from ..dto import PipeOrderDTO
from .base import BaseOrderPipe
from ..exceptions import InvalidOrderStatusPipeException

from apps.tinkoff_payments.models import TinkoffPaymentData
from apps.tinkoff_payments.services.core.api_client import TinkoffPaymentsClient
from apps.tinkoff_payments.services.payment_initialization.data_builders import (
    AdvancePaymentDataBuilder,
)
from apps.tinkoff_payments.services.payment_initialization.enums import PaymentStrategyType
from apps.tinkoff_payments.services.payment_initialization.dto import ResponsePaymentInitDTO
from apps.tinkoff_payments.services.payment_initialization.payment_initializer_service import (
    TinkoffPaymentInitializerService,
)


class ReinitPaymentSessionPipe(BaseOrderPipe):
    """
    Пайп для реинициализации платежной сессии с банком.

    Не участвует в основном пайплайне обработки заказа.
    Используется отдельно.
    """

    _ALLOWED_STATUSES: list[Order.Status] = [
        Order.Status.REJECTED,
        Order.Status.REINIT_FAILED,
        Order.Status.PAYMENT_SESSION_EXPIRED,
    ]

    @classmethod
    def get_pipe_name(cls) -> str:
        """Получение названия пайпа"""

        return 'Реинициализация платежной сессии'

    def invoke(self, order_data: PipeOrderDTO) -> None:
        """
        Запуск пайпа.

        :param order_data: Данные о заказе вместе с платежными данными.
        """

        order = order_data.order

        if not self.is_valid_status(order.status):
            raise InvalidOrderStatusPipeException(order=order, pipe=self)

        # Переведем в статус `ON_REINIT`, чтобы заказ снова стал
        # занимать период аренды, чтобы другие клиенты не могли
        # перехватить этот период.
        order.status = Order.Status.ON_REINIT
        order.save(update_fields=('status',))

        payment_data = order_data.payment_data

        try:
            # Инициализируем платежную сессию с банком.
            payment_init_dto = TinkoffPaymentInitializerService(
                api_client=TinkoffPaymentsClient(
                    base_url=config.TINKOFF_API_URL,
                    terminal_key=config.TINKOFF_TERMINAL_KEY,
                    password=config.TINKOFF_PASSWORD,
                ),
                init_data_builder=AdvancePaymentDataBuilder(),
            ).init(order, payment_data.payment_strategy)
        except Exception:
            order.status = Order.Status.REINIT_FAILED
            order.save(update_fields=('status',))
            raise

        with transaction.atomic():
            # Удаляем старые платежные данные.
            payment_data.delete()

            # Сохраняем новые платежные данные в БД.
            payment_data = self.__dto_to_model(payment_init_dto)
            payment_data.save()

            # Меняем статус заказа в зависимости от стратегии оплаты.
            if payment_data.payment_strategy == PaymentStrategyType.CARD:
                order.status = Order.Status.AWAIT_RESERVATION
            else:
                order.status = Order.Status.AWAIT_PAYMENT

            order.save(update_fields=('status',))

        self._result = PipeOrderDTO(order, payment_data)

    def __dto_to_model(self, payment_init_dto: ResponsePaymentInitDTO) -> TinkoffPaymentData:
        """
        Конвертация DTO с данными о платеже в модель.

        :param payment_init_dto: DTO-объект с данными о платеже.

        :return: Объект модели с платежными данными.
        """

        return TinkoffPaymentData(**payment_init_dto.__dict__)

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
