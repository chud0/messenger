# coding: UTF-8
"""
Клиент. Справка по ключам -h.
Пример запуска на отправление сообщений: python3 client.py -l chud0 -w
"""

import sys
sys.path.append("..")  # иначе не видел пакет jim

from socket import socket, AF_INET, SOCK_STREAM
import jim.common_classes as common_classes
import jim.config as config
import argparse
import bd_client_app
import logging
import log_config
import time
mesg_con_log = logging.getLogger("msg.cons")

# создаю парсер, и цепляю к нему три параметра
parser = argparse.ArgumentParser(description="Client for messenger")
parser.add_argument('-l', "--LGN", help="user name in chat", required=True)
parser.add_argument('-p', "--PORT", type=int, default=7777, help="port to connection on server, by default 7777")
parser.add_argument('-a', "--ADDR", default="localhost", help="server host, by default localhost")
# + группа для -r / -w
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-w", "--write", action="store_true", help="mode, or")
group.add_argument("-r", "--read", action="store_false", help="mode")

args = parser.parse_args()

PORT = args.PORT
ADDR = args.ADDR
LOGIN = args.LGN
W_MODE = args.write

MAX_RECV = 640


def client():
    with socket(AF_INET, SOCK_STREAM) as sock:  # Создать сокет TCP
        sock.connect((ADDR, PORT))   # Соединиться с сервером
        mesg_con_log.info("Client started, W_MODE: %s", str(W_MODE))
        message = common_classes.JimMessage(
            action="presence",
            time=time.time(),
            account_name=LOGIN,
            type="online",
            status="I am here!"
        )()
        sock.send(message)
        m_msg = sock.recv(MAX_RECV)
        try:
            common_classes.JimResponse(m_msg)()["response"]
        except KeyError:
            mesg_con_log.error("Сan't connect to server")
            exit()
        else:
            mesg_con_log.info("Connected to server, port: %s host: %s", PORT, ADDR)

        if W_MODE:
            inp = "hi!"
            while not inp == "exit":
                msg_time = time.time()
                if inp.split()[0] == "add_contact":
                    m_msg = common_classes.JimMessage(
                        action="add_contact",
                        user_id=inp.split()[1],
                        time=msg_time,
                    )()
                elif inp.split()[0] == "get_contacts":
                    m_msg = common_classes.JimMessage(
                        action="get_contacts",
                        time=msg_time,
                    )()
                elif inp.split()[0] == "del_contact":
                    m_msg = common_classes.JimMessage(
                        action="del_contact",
                        user_id=inp.split()[1],
                        time=msg_time,
                    )()
                else:
                    m_msg = common_classes.JimMessage(
                        action="msg",
                        time=msg_time,
                        message=inp,
                        encoding=config.CODING,
                        from_u=LOGIN,
                        to_u="all"
                    )()
                if len(inp):
                    sock.send(m_msg)
                    mesg_con_log.debug("Sent message: %s", str(m_msg))
                    bd_client_app.BDMsgHistory().save_history(msg_time, "self", inp, False)
                inp = input("MSG<<< ")
        else:
            m_msg = {"message": "debug"}
            while not m_msg["message"] == "exit exit exit":
                temp = sock.recv(MAX_RECV)
                m_msg = common_classes.JimResponse(temp)()
                mesg_con_log.debug("Received message: %s", str(m_msg))
                print("MSG>>>", m_msg["message"])
                bd_client_app.BDMsgHistory().save_history(m_msg["time"], m_msg["from_u"], m_msg["message"])

        message = common_classes.JimMessage(
            action="quit",
        )()
        sock.send(message)
        mesg_con_log.info("Client stoped")


if __name__ == '__main__':
    client()
