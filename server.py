# coding: UTF-8

import traceback
from functools import wraps
import sys
from socket import socket, AF_INET, SOCK_STREAM
import select
import common_classes
# import time
import logging
import log_config
mesg_serv_log = logging.getLogger("msg.server")
mesg_con_log = logging.getLogger("msg.cons")

try:
    PORT = int(sys.argv[sys.argv.index("-p") + 1])
except ValueError:
    PORT = 7777
try:
    ADDR = int(sys.argv[sys.argv.index("-a") + 1])
except ValueError:
    ADDR = ""


class Log():
    """Создает декоратор для логирования функции, применять с осторожностью)"""
    deco_log = logging.getLogger("msg.deco")

    def __init__(self):
        pass

    def __call__(self, func):
        @wraps(func)
        def decorated(*args, **kwargs):
            # traceback какая-то магия
            temp = [f[-2] for f in traceback.extract_stack()][-2]
            Log.deco_log.info("Функция %s была вызвана из функции %s", str(func.__name__), temp)
            return func(*args, **kwargs)
        return decorated


class Client:
    """Класс работы с клиентами, для сервера."""
    prop = dict(  # словарь параметров, перенести в общие?
        action="action",
    )
    MAX_RECV = 640  # количество байт на прием
    clients = []  # список клиентов, работаю только с ним

    def __init__(self, accept_info):
        """Подключен новый клиент"""
        self.conn, self.addr = accept_info
        self.status = ""  # статус клиента, по протоколу
        self.status_r = False  # готов прислать серверу? False/True
        self.status_w = False  # готов читать с сервера? False/True
        self.last_msg = ""  # полученное но необработанное сообщение. Переделать в очередь
        self.next_msg = ""  # сообщение к отправке. Переделать в очередь
        Client.clients.append(self)

    @Log()
    def remove(self):
        """Отключаю. Если вышел не сам, добавить в лог"""
        self.conn.close()
        Client.clients.remove(self)

    def read_requests():
        """Чтение запросов от клиентов, только готовых (status_r = True)"""
        for sock in [clnt for clnt in Client.clients if clnt.status_r]:
            try:
                sock.last_msg = common_classes.Message(sock.conn.recv(Client.MAX_RECV)).prop_dict
            except:  # не бросать так, определить тип ошибки!
                # отвалился клиент, который заявлял о готовности писать
                mesg_serv_log.warning("Lost connect %s", str(sock.addr))
                mesg_con_log.debug("Lost connect %s", str(sock.addr))
                sock.remove()
            finally:
                sock.status_r = False

    def write_responses():
        """Отправка сообщения клинтам, готовым принимать (status_w = True) если ксть что отправить"""
        for sock in [clnt for clnt in Client.clients if clnt.status_w and clnt.next_msg]:
            try:
                sock.conn.send(sock.next_msg)
            except:
                # отвалился клиент, заявлявший о готовности читать
                mesg_serv_log.warning("Lost connect %s", str(sock.addr))
                mesg_con_log.debug("Lost connect %s", str(sock.addr))
                sock.remove()
            else:
                sock.next_msg = ""
            finally:
                sock.status_w = False

    def process_msg():
        """Процесс обработки сообщений"""
        for sock in [clnt for clnt in Client.clients if clnt.last_msg]:
            mesg_con_log.debug("From %s message: %s", str(sock.addr), str(sock.last_msg))
            try:
                act = sock.last_msg[Client.prop["action"]]
            except:
                mesg_serv_log.error("Breaking message from %s", str(sock.addr))
            else:
                if act == "presence":  # вынести в словарь настроек!
                    sock.status = sock.last_msg["user"]["status"]
                    sock.next_msg = common_classes.Message({
                        "response": 200,
                        "alert": "",
                    }).message
                if act == "msg":
                    # пока не смотрю кому, отправляю всем кто готов принять
                    msg_to_wr = common_classes.Message(sock.last_msg).message  # просто пересылаю
                    for sock in [clnt for clnt in Client.clients if clnt.status_w and not clnt.next_msg]:
                        sock.next_msg = msg_to_wr  # Потенциальное место для ошибки! определять готовность
                        # нужно до обработки сообщений!!!
                if act == "quit":
                    sock.status = ""
                    sock.remove()
                    mesg_serv_log.info("Disonnected %s", str(sock.addr))
                    mesg_con_log.info("Disonnected %s", str(sock.addr))
            finally:
                sock.last_msg = ""


def mainloop():
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((ADDR, PORT))
    s.listen(5)
    s.settimeout(0.2)   # Таймаут для операций с сокетом
    mesg_serv_log.info("Server started")
    mesg_con_log.info("Server started")
    while True:
        try:
            result = s.accept()  # Проверка подключений
        except OSError as e:
            pass                     # timeout вышел
        else:
            Client(result)
            mesg_serv_log.info("Connected %s", str(Client.clients[-1].addr))
            mesg_con_log.info("Connected %s", str(Client.clients[-1].addr))
        finally:
            wait = 0
            clients = [clnt.conn for clnt in Client.clients]
            try:
                r, w, e = select.select(clients, clients, [], wait)
            except:
                pass            # Ничего не делать, если какой-то клиент отключился
            for clnt in [_cl for _cl in Client.clients if _cl.conn in r]:
                clnt.status_r = True  # заменить map -ом, убрать в класс Client?
            for clnt in [_cl for _cl in Client.clients if _cl.conn in w]:
                clnt.status_w = True

            Client.read_requests()
            Client.process_msg()
            Client.write_responses()


mesg_con_log.debug("Start server...")
mainloop()
