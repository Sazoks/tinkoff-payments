from .pipe_like import PipeLike


class PipeProcessException(Exception):
    """Исключение при работе шага"""

    def __init__(self, pipe: PipeLike, message: str = '', *args, **kwargs) -> None:
        """
        Инициализатор класса.

        :param pipe: Шаг пайплайна, на котором возникла ошибка.
        """

        self.pipe = pipe
        super().__init__(
            f'Ошибка обработки данных на шаге {pipe.__class__.__name__}\n'
            f'Детали: {message}'
        )
