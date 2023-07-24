from enum import (
    auto,
    Enum,
)


class OrderProcessStage(str, Enum):
    """Этапы обработки заказа"""

    def _generate_next_value_(
        name: str, start: int,  # noqa: N805
        count: int, last_values: list[str],
    ) -> str:
        return name.lower()

    CHECKING_EXISTS_DOCUMENTS = auto()
    VERIFY_DOCUMENTS = auto()
    CONFIRM_ORDER = auto()
