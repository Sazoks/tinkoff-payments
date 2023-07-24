from apps.rent.models import Order

from .enums import (
    QrDataType,
    PaymentStrategyType,
)
from .dto import ResponsePaymentInitDTO
from .data_builders import InitDataBuildable
from .initializers import (
    PaymentInitializable,
    TinkoffSBPInitializer,
    TinkoffPaymentInitializer,
)
from ..core.api_client import TinkoffPaymentsClient


class TinkoffPaymentInitializerService:
    """
    Сервис для инициализации платежей в Тинькофф на основе
    данных о том, что оплачивают и каким способом.

    В зависимости от способа оплаты выбирается стратегия
    оплаты (карты или СБП) и меняются параметры запросов.
    """

    def __init__(
        self,
        api_client: TinkoffPaymentsClient,
        init_data_builder: InitDataBuildable,
    ) -> None:
        """
        Инициализатор класса.

        :param api_client: Клиент для работы с API Тинькофф.
        :param init_data_builder: Объект для построения данных для тела запроса Init.
        """

        self.__api_client = api_client
        self.__init_data_builder = init_data_builder
        self.__allowed_initializers = {
            PaymentStrategyType.CARD: TinkoffPaymentInitializer(self.__api_client),
            PaymentStrategyType.SBP: TinkoffSBPInitializer(self.__api_client, QrDataType.PAYLOAD),
        }

    def init(
        self,
        order: Order,
        payment_strategy: PaymentStrategyType,
    ) -> ResponsePaymentInitDTO:
        """
        Инициализация платежной сессии с банком.

        С помощью билдера данных для запроса Init, переданного заказа
        и стратегии оплаты, совершает запрос Init к банку.

        :param order: Заказ, который нужно оплатить.
        :param payment_strategy: Способ оплаты, который выбрал пользователь.

        :return: DTO с данными о платеже.
        """

        initializer = self.__get_initializer(payment_strategy)
        init_data = self.__init_data_builder.build(order, payment_strategy)

        # Делаем запрос на инициализацию и получаем данные платежа в DTO.
        response = initializer.init(init_data)
        payment_init_dto = initializer.get_data_from_response(response)

        return payment_init_dto

    def __get_initializer(
        self,
        payment_strategy: PaymentStrategyType,
    ) -> PaymentInitializable:
        """Получение инициализатора на основе выбранной стратегии"""

        initializer = self.__allowed_initializers.get(payment_strategy)
        if initializer is None:
            raise ValueError(f'Способа оплаты {payment_strategy} не существует')

        return initializer
