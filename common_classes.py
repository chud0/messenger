# coding: UTF-8

import json


"""Здесь будет вынесен код, общий для клиента и сервера"""

CODING = "ascii"


class Message:
    """Класс сообщений, кодирует/декодирует для передачи м/у клиентом/сервером.
    :except используется для определения переданного аргумента: строка/словарь, можно заменить type -ом"""
    def __init__(self, msg):
        try:
            temp = msg["vot_i_naporolsya"]
        except TypeError:
            self.message = msg.decode(CODING)
            self.prop_dict = self.decode_message()
        except KeyError:
            self.prop_dict = msg
            self.message = self.code_message().encode(CODING)
        else:
            pass

    def decode_message(self):
        return json.loads(self.message)

    def code_message(self):
        return json.dumps(self.prop_dict)
