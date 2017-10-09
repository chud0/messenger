# coding: UTF-8

from socket import socket, AF_INET, SOCK_STREAM
import time
import common_classes
import sys
import logging
import log_config
mesg_con_log = logging.getLogger("msg.cons")

try:
    PORT = int(sys.argv[sys.argv.index("-p") + 1])
except ValueError:
    PORT = 7777
try:
    ADDR = int(sys.argv[sys.argv.index("-a") + 1])
except ValueError:
    ADDR = ""
try:
    sys.argv.index("-w")
except ValueError:
    W_MODE = False
else:
    W_MODE = True  # запустился в режиме записи, по умолчанию - чтения

MAX_RECV = 640


def client():
    with socket(AF_INET, SOCK_STREAM) as sock:  # Создать сокет TCP
        sock.connect((ADDR, PORT))   # Соединиться с сервером
        mesg_con_log.info("Client started, W_MODE: %s", str(W_MODE))
        message = common_classes.Message({
            "action": "presence",
            "time": time.time(),
            "user": {
                "account_name": "chud0",
                "status": "online",
            },
        }).message
        sock.send(message)
        m_msg = sock.recv(MAX_RECV)
        if common_classes.Message(m_msg).prop_dict["response"] == 200:
            mesg_con_log.info("Connected to server")
        else:
            mesg_con_log.error("Сan't connect to server")
            exit()
        if W_MODE:
            inp = ""
            while not inp == "exit":
                m_msg = common_classes.Message({
                    "action": "msg",
                    "time": time.time(),
                    "message": inp,
                }).message
                if len(inp):
                    sock.send(m_msg)
                    mesg_con_log.debug("Sent message: %s", str(m_msg))
                inp = input("MSG<<< ")
        else:
            m_msg = {"message": "debug"}
            while not m_msg["message"] == "exit exit exit":
                temp = sock.recv(MAX_RECV)
                m_msg = common_classes.Message(temp).prop_dict
                mesg_con_log.debug("Received message: %s", str(m_msg))
                print("MSG>>>", m_msg["message"])

        message = common_classes.Message({
            "action": "quit",
        }).message
        sock.send(message)
        mesg_con_log.info("Client stoped")


if __name__ == '__main__':
    client()
