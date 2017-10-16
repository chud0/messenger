# coding: UTF-8

import argparse
# import socketserver
import common_classes
from socket import socket, AF_INET, SOCK_STREAM
import select

import logging
import log_config
mesg_serv_log = logging.getLogger("msg.server")
mesg_con_log = logging.getLogger("msg.cons")

if __name__ == '__main__':
    # создаю парсер, и цепляю к нему два параметра
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', "--PORT", type=int, default=7777, help="port, by default 7777")
    parser.add_argument('-a', "--ADDR", default="", help="host for listening to server, by default all")
    args = parser.parse_args()

    PORT = args.PORT
    ADDR = args.ADDR
else:
    PORT = 7777
    ADDR = ""

MAX_RECV = 640


class IncomingClient():
    """Класс, обработчик подключаемых клиентов. Для сервера"""
    # все подключенные клиенты здесь, connected_clients[(addr)] = self.IncomingClient
    connected_clients = dict()

    def __init__(self, accept_info):
        """Подключен новый клиент"""
        self.conn, self.addr = accept_info
        self.status = ""  # статус клиента, по протоколу
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
            message = common_classes.Message(self.last_msg.pop()).prop_dict
            self.get_action_msg(message)

    def get_action_msg(self, message):
        """Формирует действие по полученному сообщению"""
        try:
            action = message["action"]
        except:
            response = self.get_response("400")
            self.next_msg.append(common_classes.Message(response).message)
        else:
            if action == "presence":
                # на презенс меняю статус, готовлю ответ, и закидываю в очередь на передачу
                self.status = message["user"]["status"]
                response = self.get_response("200")
                self.next_msg.append(common_classes.Message(response).message)

            elif action == "msg":
                # пересылаю всем (кроме себя)
                for clnt_next_msg_queue in [clnt.next_msg for clnt in
                                            IncomingClient.connected_clients.values() if self != clnt]:
                    clnt_next_msg_queue.append(common_classes.Message(message).message)

            elif action == "quit":
                self.status = ""
                self.remove()

    def get_response(self, response_code):
        if response_code == "200":
            answ_msg = {
                "response": 200,
                "alert": "",
            }
        elif response_code == "400":
            answ_msg = {
                "response": 400,
                "error": "Breaking response/json",
            }
        else:
            return None
        return answ_msg

    def remove(self):
        """Отключаю. Если вышел не сам, добавить в лог"""
        self.conn.close()
        IncomingClient.connected_clients.pop(self.addr)


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
                    mesg_con_log.debug("Sent msg: %s, to %s", str(outgoing_message), clnt.addr)

    def processing_messages(self):
        clients = self.get_my_clients()
        for clnt in clients:
            clnt.processing_msg()


def mainloop():
    s = Server(ADDR, PORT)
    mesg_con_log.debug("Server started")
    while True:
        s.check_connection()
        s.check_client_status()
        s.recv_messages()
        s.processing_messages()
        s.send_messages()


if __name__ == '__main__':
    mesg_con_log.debug("Start server...")
    mainloop()
