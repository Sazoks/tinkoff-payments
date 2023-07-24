from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    TypeVar,
    Generic,
)


_T = TypeVar('_T')


class PipeLike(Generic[_T], ABC):
    """Интерфейс для шага в пайплайне"""

    @abstractmethod
    def invoke(self, data: _T) -> None:
        """
        Запуск шага пайплайна.

        :param data: Обрабатываемые данные.
        """

        raise NotImplementedError()

    @abstractmethod
    def set_next(self, next_pipe: 'PipeLike') -> None:
        """
        Установка следующего шага после предыдущего для
        возможности асинхронного запуска.

        :param next_pipe: Следующий для выполнения шаг.
        """

        raise NotImplementedError()
