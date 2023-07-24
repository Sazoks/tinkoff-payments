import logging
import traceback

from django.db.models import (
    QuerySet,
    Prefetch,
)
from django.http import FileResponse
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as drf_filters

from rest_framework import mixins
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.exceptions import APIException
from rest_framework.serializers import BaseSerializer
from rest_framework.pagination import LimitOffsetPagination

from drf_spectacular.utils import extend_schema_view

from apps.users.permissions import IsManagerUser
from apps.common.utils import prepare_for_dataclass
from apps.common.serializers.during import DuringSerializer
from apps.notifications.services.senders import OrderAwaitPaymentNoticeSender

from apps.tinkoff_payments.models import TinkoffPaymentData
from apps.tinkoff_payments.serializers import PaymentDataSerializer
from apps.tinkoff_payments.services.core.exceptions import TinkoffResponseException

from ..exceptions import (
    BadGatewayAPIException,
    InvalidOrderStatusAPIException,
    OrderPipeGettingResultAPIException,
)
from ...models import (
    Order,
    RentalRate,
)
from . import openapi_schema
from ...filters import ManagerOrderFilter
from ...serializers import (
    IncomeStatisticSerializer,
    ManagerOrderListSerializer,
    ManagerOrderUpdateSerializer,
    ManagerOrderDetailSerializer,
    ManagerTinkoffInitPaymentSerializer,
    ManagerWithUserTinkoffInitPaymentSerializer,
)
from ...tasks.order import order_pipeline_task
from ...services import IncomeStatisticService
from ...services.rent.order_pipeline.pipes import (
    CancelOrderPipe,
    ConfirmOrderPipe,
    CompleteOrderPipe,
    VerifyDocumentsPipe,
    ReinitPaymentSessionPipe,
)
from ...services.rent.rental import RentalDto
from ...services.rent.order_pipeline.exceptions import (
    InvalidOrderStatusPipeException,
    NoResultOrderPipeException,
)
from ...services.rent.order_pipeline.dto import PipeOrderDTO
from ...services.docx_template import AgreementDocxTemplateService
from ...services.rent.order_pipeline.stages import OrderProcessStage
from ...services.rent.rental_validation import RentalValidationService
from ...services.rent.expired_orders_checker import ExpiredOrdersChecker
from ...services.rent.create_order_service_for_api import CreateOrderServiceForAPI


UserModel = get_user_model()

logger = logging.getLogger(__name__)


@extend_schema_view(**openapi_schema.manager_order_viewset)
class ManagerOrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class_map = {
        'list': ManagerOrderListSerializer,
        'retrieve': ManagerOrderDetailSerializer,
        'create': ManagerTinkoffInitPaymentSerializer,
        'create_with_new_user': ManagerWithUserTinkoffInitPaymentSerializer,
        'update': ManagerOrderUpdateSerializer,
        'partial_update': ManagerOrderUpdateSerializer,
        'get_income_statistic': IncomeStatisticSerializer,
    }
    permission_classes = (IsManagerUser,)
    pagination_class = LimitOffsetPagination
    filterset_class = ManagerOrderFilter
    filter_backends = [drf_filters.DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[Order]:
        return (
            Order.objects
            .with_ru_statuses()
            .select_related(
                'vehicle',
                'user__client_profile',
            )
            .prefetch_related(
                'vehicle__images',
                # Тарифы аренды сортируем по дням.
                Prefetch(
                    lookup='vehicle__rental_rates',
                    queryset=RentalRate.objects.order_by('to_days'),
                ),
            )
            .order_by('-created_at')
        )

    def get_serializer_class(self) -> type[BaseSerializer]:
        return self.serializer_class_map[self.action]

    @action(['get'], detail=False, url_path='income-statistic')
    def get_income_statistic(self, request: Request, *args, **kwargs) -> Response:
        serializer = DuringSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        during = serializer.to_representation(serializer.validated_data)
        income_statistic_dto = IncomeStatisticService(during).get_statistic()
        serializer = self.get_serializer(income_statistic_dto)

        return Response(serializer.data)

    @action(['get'], detail=True, url_path='agreement')
    def get_agreement(self, request: Request, *args, **kwargs) -> FileResponse:
        order = self.get_object()
        service = AgreementDocxTemplateService()

        return FileResponse(
            service.get(order),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )

    @action(['post'], detail=False, url_path='with-new-user')
    def create_with_new_user(self, *args, **kwargs) -> Response:
        return self.create(*args, **kwargs)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Создание нового заказа менеджером и инициализация
        платежной сессии.
        """

        serializer = self.get_serializer(data=request.data)

        # Создадим и проинициализируем заказ.
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
                except Exception:
                    raise APIException()

        # Отправим пользователю СМС и уведомление с платежной ссылкой.
        OrderAwaitPaymentNoticeSender.send(pipe_order_dto.order)

        return Response(
            data=PaymentDataSerializer(instance=pipe_order_dto.payment_data).data,
            status=status.HTTP_201_CREATED,
        )

    @action(methods=['post'], detail=True, url_path='cancel')
    def cancel(self, request: Request, *args, **kwargs) -> Response:
        """API для отмены заказа менеджером"""

        order: Order = get_object_or_404(
            klass=Order.objects.select_related('payment_data'),
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

    @action(methods=['post'], detail=True, url_path='send-for-verification')
    def send_for_verification(self, request: Request, *args, **kwargs) -> Response:
        """Отправка заказа на проверку и далее по пайплайну"""

        order: Order = self.get_object()

        # Сразу проверим, подходит ли текущий статус заказа под допустимые статусы
        # при отправке заказа на верификацию.
        if not VerifyDocumentsPipe().is_valid_status(order.status):
            raise InvalidOrderStatusAPIException(
                detail=InvalidOrderStatusPipeException.get_template_error_message().format(
                    order_id=order.pk,
                    order_status=order.status,
                    allowed_statuses=VerifyDocumentsPipe.get_allowed_statuses(),
                ),
            )

        order_pipeline_task.delay(order.pk, OrderProcessStage.VERIFY_DOCUMENTS)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True, url_path='force-confirm')
    def force_confirm(self, request: Request, *args, **kwargs) -> Response:
        """Принудительное подтверждение платежа"""

        order: Order = get_object_or_404(
            klass=Order.objects.select_related('payment_data'),
            pk=self.__get_order_id_from_url(),
        )

        try:
            ConfirmOrderPipe().invoke(PipeOrderDTO(order, order.payment_data))
        except Exception:
            logger.error(
                f'Ошибка при подтверждении заказа\nПричина: {traceback.format_exc()}'
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

    @action(methods=['post'], detail=True, url_path='complete')
    def complete(self, request: Request, *args, **kwargs) -> Response:
        """Завершение заказа"""

        order: Order = self.get_object()

        try:
            CompleteOrderPipe().invoke(PipeOrderDTO(order=order))
        except Exception:
            logger.error(
                f'Ошибка при завершении заказа\nПричина: {traceback.format_exc()}'
            )
            try:
                raise
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

    @action(methods=['post'], detail=True, url_path='send-payment-sms')
    def send_payment_sms(self, request: Request, *args, **kwargs) -> Response:
        """Отправка клиенту СМС с ссылкой на оплату"""

        # Данные должны быть свежие. Поэтому в случае, если платежная сессия
        # истекла, обновим ее.
        response = self.reinit_payment(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            raise APIException(detail=_('Ошибка при реинициализации платежной сессии'))

        # Отправка клиенту СМС и уведомления с платежной ссылкой.
        order = self.get_object()
        OrderAwaitPaymentNoticeSender.send(order)

        return Response(data=response.data, status=response.status_code)

    def __get_order_id_from_url(self) -> int:
        """Получение ID заказа из URL-параметров"""

        return int(self.kwargs[self.lookup_url_kwarg or self.lookup_field])
