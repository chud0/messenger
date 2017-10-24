# coding: UTF-8
"""Константы для работы JIM протокола"""

# Кодировка сообщений
CODING = "UTF-8"

# Возможные ключи в сообщениях от клиентов

# Коды ответов (будут дополняться)
BASIC_NOTICE = 100
OK = 200
ACCEPTED = 202
WRONG_REQUEST = 400  # неправильный запрос/json объект
SERVER_ERROR = 500

# Словарь обязательных ключей для сообщений от клиента
MANDATORY_MESSAGE_KEYS = {
    "presence": ["action", "time", "type", {"user": ["account_name", "status"]}],
    "probe": ["action", "time"],
    "msg": ["action", "time", "to_u", "from_u", "encoding", "message"],  # переделал from и to
    "quit": ["action"],
    "authenticate": ["action", "time", {"user": ["account_name", "password"]}],
    "join": ["action", "time", "room"],
    "leave": ["action", "time", "room"],
}

# Словарь обязательных ключей для ответа
MANDATORY_RESPONSE_KEYS = {
    BASIC_NOTICE: ["response", "time", "alert"],
    OK: ["response", "time", "alert"],
    ACCEPTED: ["response", "time", "alert"],
    WRONG_REQUEST: ["response", "time", "error"],
    SERVER_ERROR: ["response", "time", "error"],
}
