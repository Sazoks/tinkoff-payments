import logging
import traceback
from typing import Type

from django.conf import settings
from django.db.models import QuerySet
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404

from rest_framework import mixins
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.viewsets import GenericViewSet
from rest_framework.serializers import BaseSerializer
from rest_framework.pagination import LimitOffsetPagination

from drf_spectacular.utils import extend_schema_view

from apps.common.utils import prepare_for_dataclass

from apps.users.permissions import IsClientUser

from apps.tinkoff_payments.models import TinkoffPaymentData
from apps.tinkoff_payments.serializers import PaymentDataSerializer
from apps.tinkoff_payments.services.core.exceptions import TinkoffResponseException

from . import openapi_schema
from ...models import Order
from ...serializers.order import (
    ClientOrderListSerializer,
    ClientOrderStatusSerializer,
    ClientOrderRetrieveSerializer,
    ClientTinkoffInitPaymentSerializer,

)
from ..exceptions import (
    BadGatewayAPIException,
    InvalidOrderStatusAPIException,
    OrderPipeGettingResultAPIException,
)

from ...services.rent.rental import RentalDto
from ...services.rent.rental_validation import RentalValidationService
from ...services.rent.expired_orders_checker import ExpiredOrdersChecker

from ...services.rent.order_pipeline.pipes import (
    CancelOrderPipe,
    ReinitPaymentSessionPipe,
)
from ...services.rent.order_pipeline.exceptions import (
    NoResultOrderPipeException,
    InvalidOrderStatusPipeException,
)
from ...services.rent.order_pipeline.dto import PipeOrderDTO
from ...services.rent.create_order_service_for_api import CreateOrderServiceForAPI


logger = logging.getLogger(__name__)


@extend_schema_view(**openapi_schema.client_order_viewset)
class ClientOrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """
    Набор API для работы с заказами от лица клиента.

    Позволяет создавать заказы (и инициализировать оплату)
    и получать список заказов.
    """

    serializer_class_map = {
        'list': ClientOrderListSerializer,
        'create': ClientTinkoffInitPaymentSerializer,
        'retrieve': ClientOrderRetrieveSerializer,
        'get_status': ClientOrderStatusSerializer,
    }
    permission_classes = (IsClientUser,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self) -> QuerySet[Order]:
        """Получение заказов текущего пользователя"""

        return (
            Order.objects.select_related('user', 'vehicle')
            .filter(user=self.request.user)
            .order_by('-created_at')
        )

    def get_serializer_class(self) -> Type[BaseSerializer]:
        """Получение сериализатора на основе дейтсвия"""

        return self.serializer_class_map[self.action]

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Создание нового заказа и инициализация платежной сессии.

        Заказ создается со статусом NEW, тем самым занимая даты
        аренды автомобиля в заказе. Следовательно, другие клиенты
        не смогут выбрать эти даты для заказа, что позволит текущему
        клиенту спокойно пройти все этапы аренды автомобиля.

        В редком случае, если не удалось инициализировать платежную
        сессию с банком, заказ удаляется, тем самым освобождая даты
        для брони автомобиля.
        """

        serializer = self.get_serializer(data=request.data)

        with CreateOrderServiceForAPI(serializer) as service:
            try:
                pipe_order_dto = service.create_order_and_init_payment()
            except Exception:
                logger.error(
                    f'Ошибка инициализации платежной сессии\nПричина: {traceback.format_exc()}'
                )
                try:
                    raise
                except InvalidOrderStatusPipeException as e:
                    raise InvalidOrderStatusAPIException(detail=e.message)
                except NoResultOrderPipeException as e:
                    raise OrderPipeGettingResultAPIException(detail=e.message)
                except TinkoffResponseException as e:
                    raise BadGatewayAPIException(detail=e.message)
                except Exception as e:
                    raise APIException(
                        detail=(
                            e if settings.DEBUG
                            else APIException.default_detail
                        ),
                    )

        return Response(
            data=PaymentDataSerializer(instance=pipe_order_dto.payment_data).data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=['post'], detail=True, url_path='cancel')
    def cancel(self, request: Request, *args, **kwargs) -> Response:
        """API для отмены заказа клиентом"""

        order: Order = get_object_or_404(
            klass=Order.objects.select_related('payment_data').filter(user=request.user),
            pk=self.__get_order_id_from_url(),
        )

        try:
            CancelOrderPipe().invoke(PipeOrderDTO(order, order.payment_data))
        except Exception:
            logger.error(
                f'Ошибка при отмене заказа\nПричина: {traceback.format_exc()}'
            )
            try:
                raise
            except TinkoffResponseException as e:
                raise BadGatewayAPIException(detail=e.message)
            except InvalidOrderStatusPipeException as e:
                raise InvalidOrderStatusAPIException(detail=e.message)
            except Exception:
                raise APIException()

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='reinit-payment')
    def reinit_payment(self, request: Request, *args, **kwargs) -> Response:
        """
        Реинициализация платежной сессии.

        Если реинициализация не нужна или не может быть произведена,
        возвращает текущие платежные данные заказа.
        """

        order: Order = get_object_or_404(
            klass=(
                Order.objects
                .select_related('vehicle', 'payment_data')
                .filter(user=request.user)
            ),
            pk=self.__get_order_id_from_url(),
        )
        payment_data: TinkoffPaymentData = order.payment_data

        # Проверка заказа на истекшесть и перевод его в соответствующий статус.
        expired = ExpiredOrdersChecker.is_expired(order)

        if not ReinitPaymentSessionPipe.is_valid_status(order.status):
            raise InvalidOrderStatusAPIException(
                detail=InvalidOrderStatusPipeException.get_template_error_message().format(
                    order_id=order.pk,
                    order_status=order.status,
                    allowed_statuses=ReinitPaymentSessionPipe.get_allowed_statuses(),
                )
            )

        # Производим валидацию данных аренды. Проверяем даты.
        rental_dto = RentalDto(**prepare_for_dataclass(model_to_dict(order), RentalDto))
        RentalValidationService(order_for_exclude=order).full_validate(
            rental_dto, order.vehicle
        )

        # Проводим реинициализацию платежной сессии для заказа, если текущая истекла.
        reinit_payment_session_pipe = ReinitPaymentSessionPipe()
        try:
            reinit_payment_session_pipe.invoke(PipeOrderDTO(order, payment_data))
        except Exception:
            logger.error(
                f'Ошибка при реинициализации платежной сессии\n'
                f'Причина: {traceback.format_exc()}'
            )
            try:
                raise
            except InvalidOrderStatusPipeException as e:
                raise InvalidOrderStatusAPIException(detail=e.message)
            except TinkoffResponseException as e:
                raise BadGatewayAPIException(detail=e.message)
            except Exception:
                raise APIException()

        payment_data = reinit_payment_session_pipe.get_result().payment_data

        return Response(
            data={
                'payment_data': PaymentDataSerializer(instance=payment_data).data,
                'reinited': not expired,
            },
            status=status.HTTP_200_OK,
        )

    @action(methods=['get'], detail=True, url_path='get-status')
    def get_status(self, request: Request, *args, **kwargs) -> Response:
        """Получение статуса заказа"""

        order: Order = get_object_or_404(
            klass=Order.objects.select_related('payment_data').filter(user=request.user),
            pk=self.__get_order_id_from_url(),
        )

        # Чтобы клиент получал всегда актуальный статус заказа,
        # сразу проверим, не истекла ли платежная сессия.
        ExpiredOrdersChecker.is_expired(order)

        return Response(
            data=self.get_serializer(instance=order).data,
            status=status.HTTP_200_OK,
        )

    def __get_order_id_from_url(self) -> int:
        """Получение ID заказа из URL-параметров"""

        return int(self.kwargs[self.lookup_url_kwarg or self.lookup_field])
