from typing import (
    TypeVar,
    Callable,
)

from .pipe_like import PipeLike
from .exceptions import PipeProcessException


_T = TypeVar('_T')


class SimplePipe(PipeLike[_T]):
    """Класс простого шага для пайплайна"""

    def __init__(self, action: Callable[[_T], None]) -> None:
        """
        Инициализатор класса.

        :param action: Действие, которое должно быть выполнено.
        """

        self.__action = action
        self.__next: PipeLike | None = None

    def invoke(self, data: _T) -> None:
        """
        Запуск шага пайплайна.

        :param data: Обрабатываемые данные.
        """

        try:
            self.__action(data)
        except Exception as e:
            raise PipeProcessException(self) from e
        else:
            if self.__next is not None:
                self.__next.invoke(data)

    def set_next(self, next_pipe: PipeLike) -> None:
        """
        Установка следующего шага после предыдущего для
        возможности асинхронного запуска.

        :param next_pipe: Следующий для выполнения шаг.
        """

        self.__next = next_pipe
