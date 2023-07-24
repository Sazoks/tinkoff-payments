from typing_extensions import Self

from django.db import transaction
from rest_framework.serializers import Serializer

from ...models.order import TempBookedPeriod
from ...services.rent.order_pipeline.dto import PipeOrderDTO
from .order_pipeline.exceptions import NoResultOrderPipeException
from ...services.rent.order_pipeline.pipes import InitPaymentSessionPipe
from ...services.rent.temp_booked_period_service import TempBookedPeriodsService


class CreateOrderServiceForAPI:
    """
    Сервис-фасад для создания заказа и инициализации
    платежа к нему.

    Служит лишь для сокрытия сложностей логики в API-контроллерах.
    """

    def __init__(self, serializer: Serializer) -> None:
        """
        Инициализатор класса.

        :param serializer: Сериализатор с данными.
        """

        self.__serializer = serializer
        self.__temp_period_service: TempBookedPeriodsService | None = None
        self.__temp_booked_period: TempBookedPeriod | None = None

    def __enter__(self) -> Self:
        """Валидация данных и временное бронирование периода"""

        self.validate()
        self.book_period()

        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Освобождение временно забронированного периода"""

        self.release_period()

    def validate(self) -> None:
        """Валидация входных данных"""

        self.__serializer.is_valid(raise_exception=True)

    def book_period(self) -> None:
        """Временное бронирование периода"""

        self.__temp_period_service = TempBookedPeriodsService(
            starts_at=self.__serializer.validated_data['order']['starts_at'],
            ends_at=self.__serializer.validated_data['order']['ends_at'],
        )

        # Проверка на бронь не нужна, т.к. она заложена в сериализаторе.
        self.__temp_booked_period = self.__temp_period_service.to_book(unsafe=True)

    @transaction.atomic
    def create_order_and_init_payment(self) -> PipeOrderDTO:
        """
        Создание заказа и инициализация платежа.

        Операция выполняется в рамках одной транзакции.
        Либо создаем заказ, обновляем юзера и его профиль, если нужно, и
        инициализируем платежную сессию, либо не делаем вообще ничего.

        :return: DTO с данными заказа и платежной сессии.
        """

        new_order = self.__serializer.save()

        # Инициализация платежной сессии с банком и сохранение данных в БД.
        init_payment_pipe = InitPaymentSessionPipe(
            payment_strategy=self.__serializer.validated_data['payment_strategy'],
        )
        init_payment_pipe.invoke(PipeOrderDTO(order=new_order))

        pipe_order_dto = init_payment_pipe.get_result()
        if pipe_order_dto is None:
            raise NoResultOrderPipeException(pipe=init_payment_pipe)

        return pipe_order_dto

    def release_period(self) -> None:
        """Освобождение временно забронированного периода"""

        self.__temp_booked_period.delete()
