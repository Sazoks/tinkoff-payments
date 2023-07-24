from typing import Any

from django.db.models import Model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import empty

from apps.common.utils.string import camel_to_snake

from .models import TinkoffPaymentData
from .services.notifications.dto import TinkoffNotificationDTO
from .services.notifications.enums import NotificationPaymentStatus


class PaymentDataSerializer(serializers.ModelSerializer):
    """Сериализатор модели данных о платеже"""

    payment_session_lifetime = serializers.SerializerMethodField()

    class Meta:
        model = TinkoffPaymentData
        fields = '__all__'

    def get_payment_session_lifetime(self, obj: TinkoffPaymentData) -> int:
        """Перевод объекта `timedelta` в секунды"""

        return int(obj.payment_session_lifetime.total_seconds())


class NotificationRequestSerializer(serializers.Serializer):
    """Сериализатор для данных из уведомления от Тинькофф"""

    terminal_key = serializers.CharField(max_length=20)
    token = serializers.CharField()
    order_id = serializers.IntegerField()
    success = serializers.BooleanField()
    status = serializers.ChoiceField(choices=NotificationPaymentStatus.choices())
    payment_id = serializers.CharField(max_length=23)
    error_code = serializers.CharField(max_length=20)
    amount = serializers.IntegerField()

    def __init__(
        self,
        instance: Model | None = None,
        data: dict[str, Any] | empty = empty,
        **kwargs,
    ) -> None:
        """Инициализатор класса"""

        if data is not empty:
            # Приводим ключи в порядок и кастим значения к нужным типам.
            data = self.__keys_from_camel_to_snake(data)
            data['order_id'] = int(data['order_id'])
            data['payment_id'] = str(data['payment_id'])

        super().__init__(instance, data, **kwargs)

    def to_dto(self) -> TinkoffNotificationDTO:
        """Получение отвалидированных данных в DTO"""

        return TinkoffNotificationDTO(**self.validated_data)

    def __keys_from_camel_to_snake(self, data: dict[str, Any]) -> dict[str, Any]:
        """Получение словаря с ключами в snake_case стиле"""

        return {camel_to_snake(key): value for key, value in data.items()}


class SBPPayTestSerializer(serializers.Serializer):
    """
    Сериализатор для данных из запроса на проведение
    тестового платежа по СБП.
    """

    PaymentId = serializers.CharField(
        max_length=23,
        label=_('ID платежной сессии в банке'),
    )
    IsDeadlineExpired = serializers.BooleanField(
        required=False,
        label=_('Признак эмуляции отказа банком при таймауте'),
    )
    IsRejected = serializers.BooleanField(
        required=False,
        label=_('Признак эмуляции отказа банком в проведении платежа'),
    )
