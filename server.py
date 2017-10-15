# coding: UTF-8

import argparse
# import socketserver
import common_classes
from socket import socket, AF_INET, SOCK_STREAM
import select


# создаю парсер, и цепляю к нему два параметра
parser = argparse.ArgumentParser()
parser.add_argument('-p', "--PORT", type=int, default=7777, help="port, by default 7777")
parser.add_argument('-a', "--ADDR", default="", help="host for listening to server, by default all")
args = parser.parse_args()

PORT = args.PORT
ADDR = args.ADDR

MAX_RECV = 640

# class BasicMessengerHandler(socketserver.BaseRequestHandler):
#     """
#     Принимает запросы, обрабатывает и отправляет ответ
#     """
#
#     def handle(self):
#         # self.data = self.rfile.readline().strip()
#         self.data = self.request.recv(1024)
#         client_addr = self.client_address
#         # обработать пришедшие данные, отправить ответ


class IncomingClient():
    """Класс, обработчик подключаемых клиентов. Для сервера"""
    # все подключенные клиенты здесь, connected_clients[(addr)] = self.IncomingClient
    connected_clients = dict()

    def __init__(self, accept_info):
        """Подключен новый клиент"""
        self.conn, self.addr = accept_info
        self.status = ""  # статус клиента, по протоколу
        self.status_r = False  # готов прислать серверу? False/True
        self.status_w = False  # готов читать с сервера? False/True
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
        return answ_msg

    def remove(self):
        """Отключаю. Если вышел не сам, добавить в лог"""
        self.conn.close()
        IncomingClient.connected_clients.pop(self.addr)


def mainloop():
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((ADDR, PORT))
    s.listen(5)
    s.settimeout(0.2)   # Таймаут для операций с сокетом
    while True:
        try:
            result = s.accept()  # Проверка подключений
        except OSError as e:
            pass                     # timeout вышел
        else:
            IncomingClient(result)
        finally:
            wait = 0
            clients = [clnt.conn for clnt in IncomingClient.connected_clients.values()]
            try:
                r, w, e = select.select(clients, clients, [], wait)
            except:
                pass            # Ничего не делать, если какой-то клиент отключился
            for clnt in [_cl for _cl in IncomingClient.connected_clients.values() if _cl.conn in r]:
                incoming_msg = common_classes.Message(clnt.conn.recv(MAX_RECV)).prop_dict
                clnt.last_msg.append(incoming_msg)
                clnt.processing_msg()
            for clnt in [_cl for _cl in IncomingClient.connected_clients.values() if _cl.conn in w]:
                if clnt.next_msg:
                    clnt.next_msg.reverse()
                else:
                    continue
                for _ in range(len(clnt.next_msg)):
                    outgoing_message = clnt.next_msg.pop()
                    print("собираюсь отправить: ", outgoing_message)
                    try:
                        clnt.conn.send(outgoing_message)
                    except:
                        # отвалился клиент, заявлявший о готовности читать
                        clnt.remove()
                        break
                    else:
                        pass


mainloop()
