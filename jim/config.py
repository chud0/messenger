# coding: UTF-8
"""Константы для работы JIM протокола"""

# Кодировка сообщений
CODING = "UTF-8"

MAX_RECV = 640

# Возможные ключи в сообщениях от клиентов

# Коды ответов (будут дополняться)
BASIC_NOTICE = 100
OK = 200
ACCEPTED = 202  # применяется только для списка контактов
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
    "get_contacts": ["action", "time"],
    "contact_list": ["action", "user_id"],
    "add_contact": ["action", "user_id", "time"],
    "del_contact": ["action", "user_id", "time"],
}

# Словарь обязательных ключей для ответа
MANDATORY_RESPONSE_KEYS = {
    BASIC_NOTICE: ["response", "time", "alert"],
    OK: ["response", "time", "alert"],
    ACCEPTED: ["response", "quantity"],
    WRONG_REQUEST: ["response", "time", "error"],
    SERVER_ERROR: ["response", "time", "error"],
}
