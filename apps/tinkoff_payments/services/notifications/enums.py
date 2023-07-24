from enum import (
    auto,
    Enum,
)
from typing import (
    Any,
    Iterable,
)


class NotificationPaymentStatus(str, Enum):
    """Статусы платежей"""

    def _generate_next_value_(
        name: str, start: int,  # noqa: N805
        count: int, last_values: list[str],
    ) -> str:
        return name.upper()

    AUTHORIZED = auto()
    CONFIRMED = auto()
    PARTIAL_REVERSED = auto()
    REVERSED = auto()
    PARTIAL_REFUNDED = auto()
    REFUNDED = auto()
    REJECTED = auto()
    ATTEMPTS_EXPIRED = auto()
    CANCELED = auto()
    DEADLINE_EXPIRED = auto()

    @classmethod
    def choices(cls) -> Iterable[tuple[str, Any]]:
        return tuple((i.value, i.name) for i in cls)
