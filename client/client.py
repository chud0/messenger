# coding: UTF-8
"""
Клиент. Справка по ключам -h.
Пример запуска на отправление сообщений: python3 client.py -l chud0
Перед отправкой нужно выбрать кому отправлять: "<< login"
Для смены выбора пользователя: ">>"
Есле пользователь не выбран приглашение выглядит: "      None<<", выбран: "     login<<"
"""

import sys
sys.path.append("..")  # иначе не видел пакет jim

from queue import Queue
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM
import argparse
import bd_client_app
import jim.common_classes as common_classes
import jim.config as config
import logging
import log_config
import time
mesg_con_log = logging.getLogger("msg.cons")


class Client:
    """
    Класс клиента все необходимые методы внутри.
    Все разбито на очереди с данными и их обработка методами, но это увеличивает гибкость.
    Например, можно закидывать в очередь inp_queue команды из программы, или
    через print_queue вывоодить системные сообщения.
    """
    def __init__(self, login, addr, port):
        self.login = login  # логин клиента
        self.to_user = None  # кому передавать сообщение
        self.begin_app = True # флаг завершения приложения
        self.addr = addr
        self.port = port
        self.sock = None
        self.service_action = [key for key in config.MANDATORY_MESSAGE_KEYS.keys() if key != "msg"]
        self.print_queue = Queue()  # очередь для сообщений для печати
        self.send_queue = Queue()  # очередь для сообщений для отправки
        self.inp_queue = Queue()  # очередь для входящих сообщений
        self.answ_queue = Queue() # очередь для ожидания ответов
        self.wait_command = False  # жду ли обязательного ответа

    def inp_greetings(self):
        """Строка приветствия инпута"""
        return "{:>10}<<".format(str(self.to_user))

    def processing_inp(self):
        """
        Метод обработки инпута. Берет из инпута и складывает в очердь входящих.
        Очередь входящих нужна для того чтобы самому если нужно закидывать сообщения/команды.
        """
        while True:
            inp_str = input(self.inp_greetings())
            if len(inp_str):
                self.inp_queue.put(inp_str)

    def processing_msg(self):
        """
        Метод обработки входящих собщений из очереди.
        Сообщение проверяется на вхождение в команды, иначе считается сообщением.
        """
        while True:
            inp_str = self.inp_queue.get()
            msg_time = time.time()
            m_msg = None

            if inp_str.split()[0] in self.service_action:
                mesg_con_log.debug("Recv service msg: %s", str(inp_str))
                # значит сервисное сообщение
                if inp_str.startswith("add_contact"):
                    try:
                        user = inp_str.split()[1]  # логин вторым словом
                    except IndexError:  # нет обязательного параметра сообщение об ошибке в принт
                        self.print_queue.put(("Пропущен обязательный параметр, логин юзверя", "SYSTEM"))
                    else:
                        command = inp_str.split()[0]
                        m_msg = common_classes.JimMessage(
                            action=command,
                            user_id=user,
                            time=msg_time,
                        )()
                        # bd_client_app.BDContacts().add_contact(user)

                elif inp_str == "get_contacts":
                    command = inp_str
                    m_msg = common_classes.JimMessage(
                        action=command,
                        time=msg_time,
                    )()

                elif inp_str.startswith("del_contact"):
                    try:
                        user = inp_str.split()[1]
                    except IndexError:
                        self.print_queue.put(("Пропущен обязательный параметр, логин юзверя", "SYSTEM"))
                    else:
                        command = inp_str.split()[0]
                        m_msg = common_classes.JimMessage(
                            action=command,
                            user_id=user,
                            time=msg_time,
                        )()

                elif inp_str == "quit":
                    command = inp_str
                    m_msg = common_classes.JimMessage(
                        action=command,
                    )()
                    self.begin_app = False

                elif inp_str == "presence":
                    command = inp_str
                    m_msg = common_classes.JimMessage(
                        action=command,
                        time=time.time(),
                        account_name=self.login,
                        type="online",
                        status="I am here!"
                    )()

            elif inp_str.startswith("<<"):  # выбор юзверя для отправки сообщений
            # !!!!! проверять есть ли в списке контактов
                try:
                    user = inp_str.split()[1]
                except IndexError:
                    self.print_queue.put(("Пропущен обязательный параметр, логин юзверя", "SYSTEM"))
                else:
                    self.to_user = user

            elif inp_str == ">>":  # для смены юзверя
                self.to_user = None


            elif self.to_user != None:  # все остальное сообщения если выбрано кому передавать
                command = "msg"
                m_msg = common_classes.JimMessage(
                    action=command,
                    time=msg_time,
                    message=inp_str,
                    encoding=config.CODING,
                    from_u=self.login,
                    to_u=self.to_user
                )()

            if m_msg != None:
                self.send_queue.put((command, m_msg))
                if command == "msg":
                    bd_client_app.BDMsgHistory().save_history(msg_time, "self", inp_str, False)

    def processing_send(self):
        """
        Метод отправки сообщений. Получает из очереди.
        Заморочки только с командами требующими подтверждения.
        Механизм подтверждения реализован через очередь "answ_queue".
        """
        while True:
            msg_send = self.send_queue.get()
            self.sock.send(msg_send[1])
            mesg_con_log.debug("Sent message: %s", str(msg_send))
            # от некоторых служебных сообщений требуются ответы
            command = msg_send[0]
            if command in self.service_action:
                mesg_con_log.debug("Poluchil: %s", str(command))
                if command == "presence":
                    self.answ_queue.put(command)
                    self.answ_queue.join() # положил команду, подождал обработку, достал ответ
                    answ = self.answ_queue.get()
                    self.answ_queue.task_done()
                    if answ == config.OK:
                        mesg_con_log.info("Connected to server, port: %s host: %s", self.port, self.addr)
                    else:
                        mesg_con_log.error("Сan't connect to server")
                        self.begin_app = False
                if command == "get_contacts":
                    self.answ_queue.put(command)
                    self.answ_queue.join() # положил команду, подождал обработку, достал ответ
                    answ = self.answ_queue.get()
                    self.answ_queue.task_done()
                    if answ == config.ACCEPTED:
                        mesg_con_log.info("Contact list updated")
                    else:
                        mesg_con_log.info("Contact list NOT updated!")


    def processing_recv(self):
        """
        Метод обработки входящих сообщений.
        Заморочки только с ответами на сообщения для processing_send
        """
        while True:
            msg_recv = self.sock.recv(config.MAX_RECV)
            m_msg = common_classes.JimResponse(msg_recv)()
            mesg_con_log.debug("Received message: %s", str(m_msg))

            if not self.answ_queue.empty() and not self.wait_command:
                self.wait_command = (self.answ_queue.get(), time.time())
                self.answ_queue.task_done()

            # может быть ошибка если другой поток успеет закинуть сообщение
            if self.wait_command and (time.time() - self.wait_command[1]) > 5:
                mesg_con_log.error("Not recv response from server")
                self.begin_app = False

            try:
                message_keys = m_msg.keys()
            except AttributeError:
                pass
            else:
                if "message" in message_keys:
                    message = m_msg["message"]
                    self.print_queue.put((message, m_msg["from_u"]))
                    bd_client_app.BDMsgHistory().save_history(m_msg["time"], m_msg["from_u"], m_msg["message"])

                elif "response" in message_keys:
                    if self.wait_command:
                        command = self.wait_command[0]
                        time.sleep(0.05)  # иначе очередь может быстро получить новое сообщение
                        if self.wait_command[0] == "presence":
                            self.answ_queue.put(m_msg["response"])
                            self.answ_queue.join()
                            self.wait_command = False

                        elif self.wait_command[0] == "get_contacts":
                            self.answ_queue.put(m_msg["response"])
                            self.answ_queue.join()
                            self.wait_command = False
                            quantity = m_msg["quantity"]
                            contact_list = []

                elif "action" in message_keys:
                    message_values = m_msg.values()

                    if "contact_list" in message_values:
                        contact_list.append(m_msg["user_id"])
                        if len(contact_list) == quantity:
                            bd_client_app.BDContacts().update_contacts(contact_list)
                            self.print_queue.put((contact_list, "in your CL"))
                            quantity = 0
                            contact_list = []

    def processing_print(self):
        """
        Метод печати сообщений, все берет из очереди print_queue.
        """
        while True:
            message = self.print_queue.get()
            greetings = "{:>10}>>".format(message[1])
            print("\n", greetings, message[0], "\n", self.inp_greetings(), sep="", end="")

    def start_client(self):
        """
        Метод запуска клиента, включает все необходимые методы в процессах.
        Работает пока атрибут "begin_app" == True
        """
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.addr, self.port))   # Соединиться с сервером
        mesg_con_log.info("Client started")
        self.inp_queue.put("presence")

        func_to_start = [
            self.processing_inp,
            self.processing_send,
            self.processing_recv,
            self.processing_msg,
            self.processing_print,
        ]
        started_thread = []  # на будущее)
        for func in func_to_start:
            st_th = Thread(target=func)
            st_th.daemon = True
            st_th.start()
            started_thread.append((func, st_th))

        while self.begin_app:
            pass
        time.sleep(1)
        self.sock.close()

    def start_th_gui_client(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.addr, self.port))   # Соединиться с сервером
        mesg_con_log.info("Client started")
        self.inp_queue.put("presence")
        # self.inp_queue.put("get_contacts")

        func_to_start = [
            self.processing_send,
            self.processing_recv,
            self.processing_msg,
        ]
        started_thread = []  # на будущее)
        for func in func_to_start:
            st_th = Thread(target=func)
            st_th.daemon = True
            st_th.start()
            started_thread.append((func, st_th))


if __name__ == '__main__':

    # создаю парсер, и цепляю к нему три параметра
    parser = argparse.ArgumentParser(description="Client for messenger")
    parser.add_argument('-l', "--LGN", help="user name in chat", required=True)
    parser.add_argument('-p', "--PORT", type=int, default=7777, help="port to connection on server, by default 7777")
    parser.add_argument('-a', "--ADDR", default="localhost", help="server host, by default localhost")

    args = parser.parse_args()
    PORT = args.PORT
    ADDR = args.ADDR
    LOGIN = args.LGN

    Client(LOGIN, ADDR, PORT).start_client()
