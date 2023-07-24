from rest_framework import status
from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .serializers import SBPPayTestSerializer


sbp_pay_test = {
    'post': extend_schema(
        operation_id='sbp_pay_test',
        summary=_('Проведение тестового платежа через СБП'),
        description=_(
            'Проведение тестового платежа через СБП с предопределенным статусом.<br><br>'
            'Можно эмулировать отказ по таймауту или другой причине.<br><br>'
            'По-умолчанию эмуляция не включена и платеж будет проходить успешно.<br><br>'
            '<b>Одновременно может быть указан только один из параметров: '
            '`IsDeadlineExpired` или `IsRejected`.</b>'
        ),
        request=SBPPayTestSerializer,
        responses={
            status.HTTP_200_OK: inline_serializer(
                name='SBPPayTestResponseSerializer',
                fields={
                    'Success': serializers.BooleanField(),
                    'ErrorCode': serializers.CharField(),
                    'Message': serializers.CharField(),
                    'Details': serializers.CharField(),
                },
            ),
        },
    ),
}
