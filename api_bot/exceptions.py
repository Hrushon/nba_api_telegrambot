"""Кастомные ошибки для логирования телеграмм-бота."""


class ApiStatusTrouble(Exception):
    """Ошибка при проверке HTTP-статуса ответа от API-сервиса."""

    pass


class ApiRequestTrouble(Exception):
    """Ошибка при отправке запроса к API-сервису."""

    pass


class SendMessageFail(Exception):
    """Ошибка при отправке сообщения."""

    pass


class ResponseEmptyFail(Exception):
    """Ошибка при получении пустого ответа от сервера API."""

    pass
