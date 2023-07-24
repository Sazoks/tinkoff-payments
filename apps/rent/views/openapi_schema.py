from rest_framework import status
from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.utils.drf_spectacular.serializers import (
    ErrorWithCodeSerializer,
    FieldErrorWithCodeSerializer,
)
from apps.tinkoff_payments.serializers import PaymentDataSerializer

from ...serializers import (
    ClientOrderStatusSerializer,
    ManagerTinkoffInitPaymentSerializer,
    ManagerWithUserTinkoffInitPaymentSerializer,
)
from ...serializers.order.client import ClientTinkoffInitPaymentSerializer


manager_order_viewset = {
    'create': extend_schema(
        operation_id='manager_create_order',
        summary=_('Создание нового заказа (менеджер)'),
        description=_('Создание нового заказа от лица менеджера.'),
        request=ManagerTinkoffInitPaymentSerializer,
        responses={
            status.HTTP_201_CREATED: PaymentDataSerializer,
            status.HTTP_400_BAD_REQUEST: inline_serializer(
                name='CreateErrorManagerOrderSerializer',
                fields={
                    'payment_type': ErrorWithCodeSerializer(),
                    'order': FieldErrorWithCodeSerializer(),
                },
            ),
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
    'create_with_new_user': extend_schema(
        operation_id='manager_create_order_with_user',
        summary=_('Создание нового заказа с созданием пользователя (менеджер)'),
        description=_('Создание нового заказа от лица менеджера с регистрацией пользователя.'),
        request=ManagerWithUserTinkoffInitPaymentSerializer,
        responses={
            status.HTTP_201_CREATED: PaymentDataSerializer,
            status.HTTP_400_BAD_REQUEST: inline_serializer(
                name='CreateErrorManagerOrderSerializer1',
                fields={
                    'payment_type': ErrorWithCodeSerializer(),
                    'order': FieldErrorWithCodeSerializer(),
                },
            ),
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
    'cancel': extend_schema(
        operation_id='manager_cancel_order',
        summary=_('Отмена заказа менеджером'),
        description=_(
            'Отмена заказа менеджером.<br><br>'
            'Заказ можно отменить, если он имеет один из следующих статусов:<br>'
            '<ul>'
            '<li>`RESERVATION_SUCCESS`</li><br>'
            '<li>`PAYMENT_SUCCESS`</li><br>'
            '<li>`AWAIT_PAYMENT`</li><br>'
            '<li>`AWAIT_RESERVATION`</li><br>'
            '<li>`WITHOUT_DOCS`</li><br>'
            '<li>`VERIFY_FAILED`</li><br>'
            '<li>`CONFIRM_PAYMENT_FAILED`</li><br>'
            '<li>`BOOKED`</li><br>'
            '</ul>'
            'Если заказ находится в других статусах, отменить его не получится. '
            'Нужно будет дождаться завершения каких-либо операций, которые переведут '
            'заказ в допустимый статус.'
        ),
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
    'send_for_verification': extend_schema(
        operation_id='manager_send_order_for_verification',
        summary=_('Отправка заказа на проверку'),
        description=_(
            'Отправка заказа на проверку и далее по пайплайну.<br><br>'
            'После отправки на проверку, в случае успешной проверки, заказ автоматически '
            'пытается подтвердиться. В случае ошибки подтверждения статус заказа '
            'меняется на `CONFIRM_PAYMENT_FAILED`.<br>'
            'Заказ может быть отправлен на проверку, если он имеет один из следующих '
            'статусов:<br>'
            '<ul>'
            '<li>`PAYMENT_SUCCESS`</li><br>'
            '<li>`RESERVATION_SUCCESS`</li><br>'
            '<li>`WITHOUT_DOCS`</li><br>'
            '<li>`VERIFY_FAILED`</li><br>'
            '</ul>'
            'Если заказ находится в других статусах, отправить его на проверку не получится. '
            'Нужно будет дождаться завершения каких-либо операций, которые переведут '
            'заказ в допустимый статус.'
        ),
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
        },
    ),
    'force_confirm': extend_schema(
        operation_id='manager_force_confirm_order',
        summary=_('Принудительное подтверждение заказа'),
        description=_(
            'Позволяет выполнить запрос принудительного подтверждения заказа, '
            'минуя все проверки.<br><br>'
            'Заказ может быть принудительно подтвержден, если он имеет один из '
            'следующих статусов:<br>'
            '<ul>'
            '<li>`APPROVAL_SUCCESS`</li><br>'
            '<li>`WITHOUT_DOCS`</li><br>'
            '<li>`VERIFY_FAILED`</li><br>'
            '<li>`CONFIRM_PAYMENT_FAILED`</li><br>'
            '</ul>'
            'Если заказ находится в других статусах, принудительно подтвердить его не получится. '
            'Нужно будет дождаться завершения каких-либо операций, которые переведут '
            'заказ в допустимый статус.'
        ),
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
    'complete': extend_schema(
        operation_id='manager_complete_order',
        summary=_('Завершение заказа'),
        description=_(
            'Завершение заказа и перевод его в статус `COMPLETED`.<br><br>'
            'Заказ может быть завершен, если он имеет один из следующих статусов:<br>'
            '<ul>'
            '<li>`ACTIVE`</li>'
            '</ul>'
            'Если заказ находится в других статусах, завершить его не получится. '
            'Можно попробовать отменить заказ.'
        ),
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
        },
    ),
    'reinit_payment': extend_schema(
        operation_id='manager_reinit_payment_session',
        summary=_('Реинициализация платежной сессии для существующего заказа'),
        description=_(
            'Позволяет реинициализировать платежную сессию для существующего заказа, тем самым '
            'обновив платежные данные.<br><br>'
            'Платежную сессию у заказа можно реинициализировать, если заказ находтися в одном '
            'из следующих статусов:<br>'
            '<ul>'
            '<li>`REJECTED`</li><br>'
            '<li>`REINIT_FAILED`</li><br>'
            '<li>`PAYMENT_SESSION_EXPIRED`</li><br>'
            '</ul>'
            'Если текущая платежная сессия заказа не истекла, то вместо реинициализации '
            'будут возвращены текущие платежные данные.'
        ),
        responses={
            status.HTTP_200_OK: inline_serializer(
                name='ReinitedPaymentDataSerializer',
                fields={
                    'payment_data': PaymentDataSerializer(),
                    'reinited': serializers.BooleanField(),
                },
            ),
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
    'send_payment_sms': extend_schema(
        operation_id='manager_send_payment_sms',
        summary=_('Отправка СМС с ссылкой на оплату клиенту'),
        description=_(
            'Позволяет отправить клиенту СМС с ссылкой на оплату. '
            'Если платежная ссылка истекла, пытается реинициализировать '
            'платежную сессию для заказа и отправить СМС.'
        ),
        responses={
            status.HTTP_200_OK: inline_serializer(
                name='ReinitedPaymentDataSerializer',
                fields={
                    'payment_data': PaymentDataSerializer(),
                    'reinited': serializers.BooleanField(),
                },
            ),
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
}


client_order_viewset = {
    'create': extend_schema(
        operation_id='client_create_order',
        summary=_('Создание нового заказа (клиент)'),
        description=_('Создание нового заказа от лица клиента.'),
        request=ClientTinkoffInitPaymentSerializer,
        responses={
            status.HTTP_201_CREATED: PaymentDataSerializer,
            status.HTTP_400_BAD_REQUEST: inline_serializer(
                name='CreateErrorClientOrderSerializer',
                fields={
                    'payment_type': ErrorWithCodeSerializer(),
                    'order': FieldErrorWithCodeSerializer(),
                },
            ),
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
    'cancel': extend_schema(
        operation_id='client_cancel_order',
        summary=_('Отмена заказа клиентом'),
        description=_(
            'Отмена заказа клиентом.<br><br>'
            'Заказ можно отменить, если он имеет один из следующих статусов:<br>'
            '<ul>'
            '<li>`RESERVATION_SUCCESS`</li><br>'
            '<li>`PAYMENT_SUCCESS`</li><br>'
            '<li>`AWAIT_PAYMENT`</li><br>'
            '<li>`AWAIT_RESERVATION`</li><br>'
            '<li>`WITHOUT_DOCS`</li><br>'
            '<li>`VERIFY_FAILED`</li><br>'
            '<li>`CONFIRM_PAYMENT_FAILED`</li><br>'
            '<li>`BOOKED`</li><br>'
            '</ul>'
            'Если заказ находится в других статусах, отменить его не получится. '
            'Нужно будет дождаться завершения каких-либо операций, которые переведут '
            'заказ в допустимый статус.'
        ),
        responses={
            status.HTTP_200_OK: None,
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
    'get_status': extend_schema(
        operation_id='client_get_order_status',
        summary=_('Получение статуса заказа клиентом'),
        description=_('Получение статуса заказа клиентом.'),
        responses={
            status.HTTP_200_OK: ClientOrderStatusSerializer,
        },
    ),
    'reinit_payment': extend_schema(
        operation_id='client_reinit_payment_session',
        summary=_('Реинициализация платежной сессии для существующего заказа'),
        description=_(
            'Позволяет реинициализировать платежную сессию для существующего заказа, тем самым '
            'обновив платежные данные.<br><br>'
            'Платежную сессию у заказа можно реинициализировать, если заказ находтися в одном '
            'из следующих статусов:<br>'
            '<ul>'
            '<li>`REJECTED`</li><br>'
            '<li>`REINIT_FAILED`</li><br>'
            '<li>`PAYMENT_SESSION_EXPIRED`</li><br>'
            '</ul>'
            'Если текущая платежная сессия заказа не истекла, то вместо реинициализации '
            'будут возвращены текущие платежные данные.'
        ),
        responses={
            status.HTTP_200_OK: inline_serializer(
                name='ReinitedPaymentDataSerializer',
                fields={
                    'payment_data': PaymentDataSerializer(),
                    'reinited': serializers.BooleanField(),
                },
            ),
            status.HTTP_403_FORBIDDEN: ErrorWithCodeSerializer,
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorWithCodeSerializer,
            status.HTTP_502_BAD_GATEWAY: ErrorWithCodeSerializer,
        },
    ),
}
