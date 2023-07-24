import requests
from typing import (
    Any,
    Type,
)

from apps.common.utils.api_tools.base_api_client import BaseAPIClient

from .request_signer import TinkoffPaymentsRequestSigner


class TinkoffPaymentsClient(BaseAPIClient):
    """
    Класс для осуществления запросов к API платежей Тинькофф.

    Каждый запрос необходимо подписывать по алгоритму, заложенному
    в `TinkoffPaymentsRequestSigner`.
    """

    _default_signer_class: Type[TinkoffPaymentsRequestSigner] = TinkoffPaymentsRequestSigner

    def __init__(
        self,
        base_url: str,
        terminal_key: str,
        password: str,
        signer: TinkoffPaymentsRequestSigner | None = None,
    ) -> None:
        """
        Инициализатор класса.

        :param base_url: Базовый URL для запросов к API.
        :param terminal_key: Ключ терминала, куда будут производиться платежи.
        :param password: Пароль от терминала.
        :param signer:
            Объект для подписи запросов в целях безопасности.
            Если None, используется подписчик запросов по умолчанию.
        """

        super().__init__(base_url)

        self.__terminal_key = terminal_key
        self.__password = password
        self.__signer = signer or self._default_signer_class(self.__password)

    def _get_default_request_data(self, request: requests.Request) -> dict[str, Any]:
        """
        Получение дополнительных данных для тела запроса.

        :param request: Обрабатываемый запрос.
        """

        data_copy: dict[str, Any] = (request.json or request.data).copy()
        data_copy['TerminalKey'] = self.__terminal_key

        # К каждому запросу добавляем ключ терминала и генерируем для
        # переданных данных подпись.
        return {
            'TerminalKey': self.__terminal_key,
            'Token': self.__signer.generate_sign(data_copy),
        }

    def _is_unauthorized_request(self, response: requests.Response) -> bool:
        """
        Классическая авторизация не используется.
        Вместо этого подписываем каждый запрос по алгоритму.
        Отключим проверку для неавторизированных запросов.
        """

        return False
