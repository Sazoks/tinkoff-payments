import logging
import traceback

from constance import config
from django.http import HttpResponse

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from drf_spectacular.utils import extend_schema_view

from .serializers import (
    SBPPayTestSerializer,
    NotificationRequestSerializer,
)
from . import openapi_schema
from .models import TinkoffPaymentData
from .services.core.endpoints import TinkoffRoutes
from .services.core.api_client import TinkoffPaymentsClient
from .services.notifications.handlers.factory import TinkoffNotificationHandlerFactory


logger = logging.getLogger(__name__)


class NotificationReceiverAPIView(GenericAPIView):
    """API для приёма уведомлений от Тинькофф со статусами платежей"""

    http_method_names = ['post']

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Обработчик POST-запросов"""

        serializer = NotificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.to_dto()

        try:
            handler = TinkoffNotificationHandlerFactory.create(notification.status)
            if handler is not None:
                handler.handle(notification)
        except Exception:
            logger.error(
                f'Ошибка отправки нотификации на обработку\n'
                f'Данные нотификации: {notification}\n'
                f'Причина: {traceback.format_exc()}'
            )
            return HttpResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return HttpResponse(content='OK', status=status.HTTP_200_OK)


@extend_schema_view(**openapi_schema.sbp_pay_test)
class SBPPayTestAPIView(GenericAPIView):
    """API для тестов оплаты через СБП"""

    http_method_names = ['post']
    lookup_url_kwarg = 'payment_id'
    serializer_class = SBPPayTestSerializer
    queryset = TinkoffPaymentData.objects.all()

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Обработчик POST-запросов"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = TinkoffPaymentsClient(
            base_url=config.TINKOFF_API_URL,
            terminal_key=config.TINKOFF_TERMINAL_KEY,
            password=config.TINKOFF_PASSWORD,
        ).request(
            method='post',
            url_postfix=TinkoffRoutes.SBP_PAY_TEST,
            data=serializer.data,
        )

        return Response(data=response.json(), status=response.status_code)
