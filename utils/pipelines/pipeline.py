from typing import TypeVar
from typing_extensions import Self

from .pipe_like import PipeLike
from .simple_pipe import SimplePipe


_T = TypeVar('_T')


class Pipeline(PipeLike[_T]):
    """Класс пайплайна"""

    def __init__(self) -> None:
        """Инициализатор класса"""

        self.__pipes: list[PipeLike] = []
        self.__terminate: PipeLike = SimplePipe(lambda data: None)

    def pipe(self, new_pipe: PipeLike) -> Self:
        """
        Добавление нового шага в пайплайн.

        :param new_pipe: Новый шаг для пайплайна.
        """

        # Последний шаг в пайплайне всегда должен указывать
        # на шаг-терминатор.
        new_pipe.set_next(self.__terminate)

        # Если это не первый шаг в пайплайне, связываем
        # последний шаг с новым.
        if len(self.__pipes) > 0:
            self.__pipes[-1].set_next(new_pipe)

        self.__pipes.append(new_pipe)

        return self

    def invoke(self, data: _T) -> None:
        """
        Запуск шага пайплайна.

        :param data: Обрабатываемые данные.
        """

        first_pipe = self.__pipes[0] if len(self.__pipes) > 0 else self.__terminate
        first_pipe.invoke(data)

    def set_next(self, next_pipe: PipeLike) -> None:
        """
        Установка следующего шага.

        Мы можем захотеть после выполнения этого пайплайна запустить
        выполнение другого пайплайна. Это должно быть сделано после
        вызова шага-терминатора текущего пайплайна.

        :param next_pipe: Следующий для выполнения шаг.
        """

        self.__terminate.set_next(next_pipe)
