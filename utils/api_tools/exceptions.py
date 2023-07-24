import requests


class APIResponseException(Exception):
    """Исключение при запросе к внешнему API"""

    def __init__(self, response: requests.Response, message: str | None = None) -> None:
        """
        Инициализатор класса.

        :param response: Ответ сервера.
        :param message: Сообщение об ошибке.
        """

        self.message = message or self.__build_message(response)
        self.response = response

        super().__init__(self.message)

    def __build_message(self, response: requests.Response) -> str:
        """
        Построение сообщения об ошибке на основе ответа.

        :param response: Ответ сервера.
        """

        return (
            f'\nОшибка при запросе к внешнему API\n'
            f'Метод: {response.request.method}\n'
            f'URL: {response.request.url}\n'
            f'Детали: {response.content.decode()}'
        )
