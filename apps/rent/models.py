from django.db import models
from django.utils.translation import ugettext_lazy as _

from apps.common.constants import (
    Discount,
    FieldConstraint,
)
from apps.rent.constants import District
from apps.rent.managers import OrderManager


class Order(models.Model):
    """Модель заказа"""

    class Status(models.TextChoices):
        """Статусы заказа"""

        NEW = 'NEW', _('Новый заказ')
        AWAIT_PAYMENT = 'AWAIT_PAYMENT', _('Ожидание оплаты')
        AWAIT_RESERVATION = 'AWAIT_RESERVATION', _('Ожидание резервации')
        RESERVATION_SUCCESS = 'RESERVATION_SUCCESS', _('Резервация успешна')
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', _('Оплачено')
        WITHOUT_DOCS = 'WITHOUT_DOCS', _('Без документов')
        ON_APPROVAL = 'ON_APPROVAL', _('Проверка документов')
        APPROVAL_SUCCESS = 'APPROVAL_SUCCESS', _('Документы успешно проверены')
        VERIFY_FAILED = 'VERIFY_FAILED', _('Ошибка проверки документов')
        AWAIT_CONFIRM_PAYMENT = 'AWAIT_CONFIRM_PAYMENT', _('Подтверждение платежа')
        CONFIRM_PAYMENT_FAILED = 'CONFIRM_PAYMENT_FAILED', _('Ошибка подтверждения платежа')
        BOOKED = 'BOOKED', _('Забронирован')
        ACTIVE = 'ACTIVE', _('Активен')
        COMPLETED = 'COMPLETED', _('Завершен')
        CANCELED = 'CANCELED', _('Отменен')
        REJECTED = 'REJECTED', _('Отклонен банком')
        ON_REINIT = 'ON_REINIT', _('На реинициализации')
        REINIT_FAILED = 'REINIT_FAILED', _('Ошибка реинициализации платежной сессии')
        PAYMENT_SESSION_EXPIRED = 'PAYMENT_SESSION_EXPIRED', _('Платежная сессия истекла')

    status = models.CharField(
        max_length=23,
        default=Status.NEW,
        choices=Status.choices,
        verbose_name=_('Status'),
    )
    with_manager = models.BooleanField(
        default=False,
        verbose_name=_('With manager'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created at'),
    )
    amount = models.DecimalField(
        max_digits=FieldConstraint.MONEY_DECIMAL_DIGITS,
        decimal_places=FieldConstraint.MONEY_DECIMAL_PLACES,
        verbose_name=_('Amount'),
    )
    discount = models.PositiveSmallIntegerField(
        choices=Discount.choices,
        default=Discount.DISCOUNT_0,
        verbose_name='Скидка аренды',
    )
    starts_at = models.DateTimeField(
        verbose_name=_('Starts at'),
    )
    ends_at = models.DateTimeField(
        verbose_name=_('Ends at'),
    )
    pickup_location = models.TextField(
        blank=True,
        verbose_name=_('Pickup location'),
    )
    pickup_district = models.CharField(
        max_length=40,
        choices=District.choices,
        verbose_name=_('Pickup district'),
    )
    return_location = models.TextField(
        blank=True,
        verbose_name=_('Return location'),
    )
    return_district = models.CharField(
        max_length=40,
        choices=District.choices,
        verbose_name=_('Return district'),
    )
    vehicle = models.ForeignKey(
        'rent.Vehicle',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Vehicle'),
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('User'),
    )

    objects = OrderManager()

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def __str__(self):
        return f'{self.vehicle.model} {self.status} {self.starts_at} {self.ends_at}'

    @property
    def is_created(self) -> bool:
        return self.pk is None

    @property
    def is_self_pickup(self) -> bool:
        return self.pickup_district == District.PICKUP

    @property
    def is_self_return(self) -> bool:
        return self.return_district == District.PICKUP


# NOTE: Более лучшее решение было бы - полностью разделить
#   периоды брони и заказы. Тогда мы бы имели возможность
#   управлять периодами брони и связывать их с нужными заказами
#   независимо друг от друга. Мы бы могли бронировать периоды
#   без создания заказов. Эта модель, своего рода, костыль.
#   Нужна, чтобы при создании нового заказа сразу забронировать
#   период без создания заказа, чтобы никто не мог его перехватить.
class TempBookedPeriod(models.Model):
    """
    Модель временно забронированного периода.

    Служит для бронирования определенных периодов
    без создания заказов.
    Учитывается в сервисе `BookingCalendarService`.
    """

    starts_at = models.DateTimeField(
        verbose_name=_('Starts at'),
    )
    ends_at = models.DateTimeField(
        verbose_name=_('Ends at'),
    )

    class Meta:
        verbose_name = _('Temporarily booked date')
        verbose_name_plural = _('Temporarily booked dates')

    def __str__(self) -> str:
        return f'{self.starts_at.date()} - {self.ends_at.date()}'
