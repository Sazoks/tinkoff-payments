import requests
from typing import Any
from typing_extensions import Self

from .http_statuses import HTTPStatus


class BaseAPIClient:
    """
    Базовый класс для API клиентов.

    Определяет базовую логику работы с внешним API.

    Позволяет к каждому запросу добавлять свои заголовки, параметры и данные.
    Также позволяет реализовать логику авторизации в случае неавторизованного запроса.
    Также позволяет слать запросы в рамках одной сессии, делать настройка по
    умолчанию для сессий и использовать свои кастомные сессии.
    """

    _REQUESTS_THAT_HAVE_BODY = ("post", "put", "putch")

    def __init__(self, base_url: str) -> None:
        """
        Инициализатор класса.

        :param base_url: Базовый URL внешнего сервиса.
        """

        self._base_url = base_url
        self._session: requests.Session | None = None

    @property
    def base_url(self) -> str:
        return self._base_url

    def request(
        self,
        method: str,
        url_postfix: str,
        data: dict[str, Any] | None = None,
        is_json: bool = True,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        session: requests.Session | None = None,
    ) -> requests.Response:
        """
        Метод отправки запроса на указанный эндпоинт.

        В случае неавторизованного запроса производит авторизацию и
        повторяет запрос.

        :param method: HTTP-метод запроса.
        :param url_postfix: Маршрут эндпоинта.
        :param data: Данные для тела запроса.
        :param is_json:
            Говорит о том, что данные для тела запроса необходимо обработать, как JSON.
        :param params: GET-параметры запроса.
        :param headers: Дополнительные заголовки запроса.
        :param session:
            Объект сессии, если хотим контролировать запросы через свою сессию.
            Если None, для каждого запроса используется своя сессия либо сессия,
            инициализированная в контекстном менеджере.

        :return: Объект ответа `requests.Response`.
        """

        # Делаем запрос.
        response = self.__request(method, url_postfix, data, is_json, params, headers, session)

        # Если запрос был неавторизированным, производим авторизационный запрос
        # и повторяем исходный запрос.
        if self._is_unauthorized_request(response):
            self._authorization()
            response = self.__request(method, url_postfix, data, is_json, params, headers, session)

        return response

    def __request(
        self,
        method: str,
        url_postfix: str,
        data: dict[str, Any] | None = None,
        is_json: bool = True,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        session: requests.Session | None = None,
    ) -> requests.Response:
        """Базовый метод отправки запроса на указанный эндпоинт"""

        request = requests.Request(
            method=method,
            params=params,
            headers=headers,
        )

        # Если есть данные для тела запроса и если метод поддерживает эти данные,
        # добавим их в тело запроса.
        if data is not None:
            if not self._has_request_body(method):
                raise ValueError(
                    f"HTTP метод {method.upper()} не поддерживает данные для тела запроса."
                )

            # TODO: Момент с данными продумать лучше.
            if is_json:
                request.json = data
                request.json |= self._get_default_request_data(request)
            else:
                request.data = data
                request.data |= self._get_default_request_data(request)

        # Добавление доп. параметров и заголовков к запросу.
        request.headers |= self._get_default_request_headers(request)
        request.params |= self._get_default_request_params(request)

        # Получаем полный URL-адрес до эндпоинта во внешнем сервисе.
        request.url = self._get_full_url(url_postfix)

        # Берем либо сессию пользователя, либо ранее инициализированную сессию.
        # Ранее инициализированная сессия контролируется в методах протокола
        # контекстного менеджера __enter__ и __exit__.
        current_session = session or self._session

        # Если не было предоставлено сессии от пользователя или ранее
        # инициализированной сессии, создадим одноразовую сессию для запроса.
        is_onetime_session = False
        if current_session is None:
            current_session = requests.Session()
            self._setup_session(current_session)
            is_onetime_session = True

        response = current_session.send(request.prepare())

        if is_onetime_session:
            current_session.close()

        return response

    def _authorization(self) -> None:
        """Метод для проведения авторизации во внешнем сервисе"""

        pass

    def _setup_session(self, session: requests.Session) -> None:
        """
        Дополнительная настройка внутреннего объекта сессии для запросов.

        Объекты сессий, которые пользователь может сам передавать в каждый
        запрос, не модифицируются данным методом.
        """

        pass

    def _get_default_request_headers(self, request: requests.Request) -> dict[str, Any]:
        """
        Получение доп. заголовков для запроса.

        Позволяет добавлять к каждому запросу доп. заголовки.

        :param request: Объект обрабатываемого запроса.
        """

        return {}

    def _get_default_request_params(self, request: requests.Request) -> dict[str, Any]:
        """
        Получение доп. GET-параметров для запроса.

        Позволяет добавлять к каждому запросу доп. GET-параметры.

        :param request: Объект обрабатываемого запроса.
        """

        return {}

    def _get_default_request_data(self, request: requests.Request) -> dict[str, Any]:
        """
        Получение доп. данных для тела запроса.

        Позволяет добавлять к каждому запросу, который имеет тело, доп. данные.

        :param request: Объект обрабатываемого запроса.
        """

        return {}

    def _is_unauthorized_request(self, response: requests.Response) -> bool:
        """
        Метод, позволяющий определить, являлся ли запрос неавторизованным на
        основе полученного ответа.

        :param response: Объект синхронного ответа `requests.Response`.

        :return: True, если запрос был неавторизованным. Иначе False.
        """

        return response.status_code == HTTPStatus.HTTP_401_UNAUTHORIZED

    @classmethod
    def _has_request_body(cls, method: str) -> bool:
        """
        Проверка, имеет ли запрос с методом `method` тело для данных.

        :param method: HTTP-метод.

        :return: True, если запрос с методом `method` имеет тело, иначе False.
        """

        return method.lower() in cls._REQUESTS_THAT_HAVE_BODY

    def _get_full_url(self, url_postfix: str) -> str:
        """
        Создание полного URL-адреса для запроса с проверками.

        :param url_postfix: Эндпоинт API внешнего сервиса.

        :return: Полный URL-адрес для запроса.
        """

        # Убираем лишние слешы, если они есть.
        if url_postfix.startswith("/"):
            url_postfix = url_postfix[1:]

        base_url = self._base_url
        if base_url.endswith("/"):
            base_url = base_url[:-1]

        return base_url + "/" + url_postfix

    def __enter__(self) -> Self:
        """Инициализация сессии для запросов"""

        self._session = requests.Session()
        self._setup_session(self._session)

        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Закрытие и уничтожение сессии"""

        self._session.close()
        self._session = None
