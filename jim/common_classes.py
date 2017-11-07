# coding: UTF-8

from . import config
import json


class Message():
    """
    Класс сообщений, кодирует/декодирует для передачи м/у клиентом/сервером.
    Ожидает байты или словарь. Делает проверки, ошибка всегда в словаре сообщения.
    Если не может раскодировать до словаря, формирует ответ об ошибке.
    """
    __slots__ = ["message", "prop_dict"]

    def __init__(self, msg):
        try:
            temp = str(msg, config.CODING)
        except TypeError:
            try:
                msg.keys()  # проверка на dict
            except AttributeError:  # таких сообщений приходить не должно, для тестов
                self.prop_dict = {"ERROR": config.SERVER_ERROR, "message": "incorrect type msg"}
            else:
                self.message = bytes(json.dumps(msg), config.CODING).ljust(config.MAX_RECV)
                self.prop_dict = msg
        except UnicodeDecodeError:
            self.message = msg
            self.prop_dict = {"ERROR": config.WRONG_REQUEST, "message": "incorrect encoding"}
        else:
            self.message = msg
            temp = temp.rstrip()
            try:
                temp = json.loads(temp)
            except json.JSONDecodeError:
                self.prop_dict = {"ERROR": config.WRONG_REQUEST, "message": "incorrect JSON object"}
            else:
                self.prop_dict = temp


class JimMessage():
    """
    Класс исходящего сообщения, принимает именованные переменные, расталкивает по атрибутам.
    Затем смотрит в модуль config, в соответствии со словарями составляет сообщение.
    Готовит к отправке через класс Message.
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __call__(self):
        ret_dict = {}
        try:
            self.__dict__["action"]
        except KeyError:  # значит это ответ
            key = getattr(self, "response")
            for attr in config.MANDATORY_RESPONSE_KEYS[key]:
                ret_dict[attr] = getattr(self, attr)
        else:
            key = getattr(self, "action")
            for attr in config.MANDATORY_MESSAGE_KEYS[key]:
                if isinstance(attr, str):
                    ret_dict[attr] = getattr(self, attr)
                else:  # добрались до словаря
                    ins_dict = {}
                    for ins_attr in list(attr.values())[0]:
                        ins_dict[ins_attr] = getattr(self, ins_attr)
                    ret_dict[list(attr.keys())[0]] = ins_dict
        return Message(ret_dict).message


class JimResponse():
    """
    Класс входящего сообщения, принимает строку байтов и преобразует классом Message.
    Возвращает словарь аргументов, без вложений.
    """
    def __init__(self, msg):
        self.message = msg

    def __call__(self):
        ret_dict = {}
        msg_dict = Message(self.message).prop_dict
        for key, value in msg_dict.items():
            if not isinstance(value, dict):
                ret_dict[key] = value
            else:
                for in_key, in_value in value.items():
                    ret_dict[in_key] = in_value
        return ret_dict
