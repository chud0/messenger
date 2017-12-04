# coding: UTF-8
# import socketserver

import sys
sys.path.append("..")  # иначе не видел пакет jim

from socket import socket, AF_INET, SOCK_STREAM
import argparse
import bd_server_app as bd
import jim.common_classes as common_classes
import jim.config as config
import logging
import log_config
import select
import time

mesg_serv_log = logging.getLogger("msg.server")
mesg_con_log = logging.getLogger("msg.cons")

MAX_RECV = 640


class IncomingClient():
    """Класс, обработчик подключаемых клиентов. Для сервера"""
    # все подключенные клиенты здесь, connected_clients[(addr)] = self.IncomingClient
    # переделал на connected_clients[логин клиента] = self.IncomingClient
    connected_clients = dict()

    def __init__(self, accept_info):
        """Подключен новый клиент"""
        self.conn, self.addr = accept_info
        self.status = ""  # статус клиента, по протоколу
        self.delete = False  # True - удаляю чтоб не мешался
        self.account_name = ""  # логин клиента
        self.last_msg = []  # полученные но необработанное сообщения
        self.next_msg = []  # сообщения к отправке
        IncomingClient.connected_clients[self.addr] = self

    def processing_msg(self):
        """Проходит по списку полученных сообщений, передает в обработку"""
        if len(self.last_msg):
            self.last_msg.reverse()
        else:
            return None
        for _ in range(len(self.last_msg)):
            message = common_classes.JimResponse(self.last_msg.pop())()
            self.get_action_msg(message)

    def get_action_msg(self, message):
        """Формирует действие по полученному сообщению"""
        try:
            action = message["action"]
        except KeyError:
            response = self.get_response(message["ERROR"], err_msg=message["message"])
            self.next_msg.append(response)
        else:
            if action == "presence":
                # на презенс меняю статус, готовлю ответ, и закидываю в очередь на передачу
                self.status = message["type"]
                # если есть такой в базе
                if bd.BDUsers().check_user(message["account_name"]):
                    response = self.get_response(config.OK)

                    self.account_name = message["account_name"]  # присваиваю клиенту логин из сообщения
                    IncomingClient.connected_clients[self.account_name] = self
                    IncomingClient.connected_clients.pop(self.addr)
                    mesg_con_log.debug("Presence from %s", self.account_name)
                    bd.BDHistory().add_entry(time.time(), self.account_name, self.addr[0])  # в базу истории
                else:
                    response = self.get_response(config.WRONG_AUTHORIZATION)
                    self.delete = True
                self.next_msg.append(response)

            elif action == "msg":
                # пересылаю сообщение если адресат в контакт листе
                to_user = message["to_u"]
                if to_user in bd.BDCList().get_list(self.account_name):
                    IncomingClient.connected_clients[to_user].next_msg.append(common_classes.Message(message).message)
                else:
                    response = self.get_response(config.WRONG_ADDRESSEE, err_msg="User not in your contact list")
                    self.next_msg.append(response)

            elif action == "get_contacts":
                # передать список конактов
                contact_list = bd.BDCList().get_list(self.account_name)
                response = self.get_response(config.ACCEPTED, attr=len(contact_list))
                self.next_msg.append(response)
                for user in contact_list:
                    message = common_classes.JimMessage(
                        action="contact_list",
                        user_id=user
                    )()
                    self.next_msg.append(message)

            elif action == "add_contact":
                # добавить в список контактов
                client = message["user_id"]
                if bd.BDCList().add_client(self.account_name, client):
                    response = self.get_response(config.OK)
                else:
                    response = self.get_response(config.SERVER_ERROR, err_msg="User not found")
                self.next_msg.append(response)

            elif action == "del_contact":
                client = message["user_id"]
                if bd.BDCList().remove_client(self.account_name, client):
                    response = self.get_response(config.OK)
                else:
                    response = self.get_response(config.SERVER_ERROR, err_msg="User not find")
                self.next_msg.append(response)

            elif action == "quit":
                self.status = ""
                self.remove()

    def get_response(self, response_code, err_msg="", attr=""):
        if response_code == config.ACCEPTED:
            answ_msg = common_classes.JimMessage(
                response=response_code,
                quantity=attr,
            )
        else:
            answ_msg = common_classes.JimMessage(
                response=response_code,
                time=time.time(),
                alert=err_msg,
                error=err_msg,
            )
        return answ_msg()

    def remove(self):
        """Отключаю. Если вышел не сам, добавить в лог"""
        self.conn.close()
        try:
            IncomingClient.connected_clients.pop(self.account_name)
        except KeyError:
            try:
                IncomingClient.connected_clients.pop(self.addr)
            except KeyError:
                pass


class Server(IncomingClient):
    """Класс сервера"""
    my_clnt = []

    def __init__(self, addr, port):
        self.ready_to_read = []
        self.ready_to_write = []
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind((addr, port))
        self.socket.listen(5)
        self.socket.settimeout(0.2)   # Таймаут для операций с сокетом

    def check_connection(self):
        """Проверка подключений"""
        try:
            result = self.socket.accept()
        except OSError:
            pass  # timeout вышел
        else:
            new_client = IncomingClient(result)
            Server.my_clnt.append(new_client)
            mesg_con_log.info("Connected %s", str(Server.my_clnt[-1].addr))

    def get_clients_connection(self):
        return [clnt.conn for clnt in self.get_my_clients()]

    def get_my_clients(self):
        return [clnt for clnt in Server.my_clnt if clnt in IncomingClient.connected_clients.values()]

    def check_client_status(self):
        clients = self.get_clients_connection()
        wait = 0
        try:
            read, write, exc = select.select(clients, clients, [], wait)
        except:
            pass  # Ничего не делать, если какой-то клиент отключился
        finally:
            self.ready_to_read = [_cl for _cl in self.get_my_clients() if _cl.conn in read]  # клиенты, готовы отправить серверу
            self.ready_to_write = [_cl for _cl in self.get_my_clients() if _cl.conn in write]  # клиенты, готовы принять

    def recv_messages(self):
        """принимает сообщения"""
        for _ in range(len(self.ready_to_read)):
            clnt = self.ready_to_read.pop()
            try:
                incoming_msg = common_classes.Message(clnt.conn.recv(MAX_RECV)).prop_dict
            except ConnectionResetError:
                # отвалился клиент, заявлявший о готовности писать
                clnt.remove()
            else:
                clnt.last_msg.append(incoming_msg)
                mesg_con_log.debug("Received msg: %s, from %s", str(incoming_msg), clnt.addr)

    def send_messages(self):
        """отправляет сообщения"""
        for _ in range(len(self.ready_to_write)):
            clnt = self.ready_to_write.pop()
            if clnt.next_msg:
                clnt.next_msg.reverse()
            else:
                continue
            for _ in range(len(clnt.next_msg)):
                outgoing_message = clnt.next_msg.pop()
                try:
                    clnt.conn.send(outgoing_message)
                except:
                    clnt.remove()
                    break
                else:
                    mesg_con_log.debug("Sent msg: %s, to %s", str(outgoing_message).rstrip(), clnt.addr)

    def processing_messages(self):
        clients = self.get_my_clients()
        for clnt in clients:
            clnt.processing_msg()

    def processing_clients(self):
        # удаляю помеченные к удалению
        clients = self.get_my_clients()
        for clnt in clients:
            if clnt.delete:
                clnt.remove()


def mainloop():
    s = Server(ADDR, PORT)
    mesg_con_log.debug("Server started")
    while True:
        s.check_connection()
        s.check_client_status()
        s.recv_messages()
        s.processing_messages()
        s.send_messages()
        s.processing_clients()


if __name__ == '__main__':
    # создаю парсер, и цепляю к нему два параметра
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', "--PORT", type=int, default=7777, help="port, by default 7777")
    parser.add_argument('-a', "--ADDR", default="", help="host for listening to server, by default all")
    args = parser.parse_args()

    PORT = args.PORT
    ADDR = args.ADDR

    mesg_con_log.debug("Start server...")
    mainloop()

else:
    PORT = 7777
    ADDR = ""
