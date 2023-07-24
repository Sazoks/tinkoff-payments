from django.urls import path

from . import views


app_name = 'api_tinkoff_payments'
urlpatterns = [
    path(
        route='notifications/',
        view=views.NotificationReceiverAPIView.as_view(),
        name='notifications',
    ),
    path(
        route='sbp-pay-test/',
        view=views.SBPPayTestAPIView.as_view(),
        name='sbp_pay_test',
    ),
]
