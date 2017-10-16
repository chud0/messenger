# coding: UTF-8

from socket import socket, AF_INET, SOCK_STREAM
import time
import common_classes
import argparse
import logging
import log_config
mesg_con_log = logging.getLogger("msg.cons")

# создаю парсер, и цепляю к нему два параметра
parser = argparse.ArgumentParser(description="client for messanger")
parser.add_argument('-p', "--PORT", type=int, default=7777, help="port to connection on server, by default 7777")
parser.add_argument('-a', "--ADDR", default="localhost", help="server host, by default localhost")
# + группа для -r / -w
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-w", "--write", action="store_true", help="mode, or")
group.add_argument("-r", "--read", action="store_false", help="mode")

args = parser.parse_args()

PORT = args.PORT
ADDR = args.ADDR
W_MODE = args.write

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
        print(m_msg)
        if common_classes.Message(m_msg).prop_dict["response"] == 200:
            mesg_con_log.info("Connected to server, port: %s host: %s", PORT, ADDR)
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
