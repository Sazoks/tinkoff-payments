from requests import Response
from apps.common.utils.api_tools.exceptions import APIResponseException


class TinkoffResponseException(APIResponseException):
    """Исключение при запросе Init"""

    def __init__(self, response: Response, message: str | None = None) -> None:
        super().__init__(response, message)
