# coding: UTF-8

import logging
from logging import handlers
import sys

# формат сообщения
formatter = logging.Formatter("%(asctime).19s %(levelname)-10s mod: %(module)-10s func: %(funcName)-12s %(message)s")
con_form = logging.Formatter("%(asctime).19s %(levelname)-10s %(message)s")
deco_form = logging.Formatter("%(asctime).19s %(message)s")

# обработчик с ежедневной ротацией лог файлов
filename = "messenger.log"
eday_log_hand = logging.handlers.TimedRotatingFileHandler(filename, when="midnight", interval=1)
eday_log_hand.suffix = "_%Y-%m-%d"
eday_log_hand.setFormatter(formatter)

# обработчик в stderr
con_hand = logging.StreamHandler(sys.stderr)
con_hand.setFormatter(con_form)

# обработчик записи в файл, для декоратора
deco_hand = logging.FileHandler("deco.log")
deco_hand.setFormatter(deco_form)

# регистратор для server
mesg_serv_log = logging.getLogger("msg.server")
mesg_serv_log.setLevel(logging.INFO)
mesg_serv_log.addHandler(eday_log_hand)

# регистратор для дебага
mesg_con_log = logging.getLogger("msg.cons")
mesg_con_log.setLevel(logging.DEBUG)
mesg_con_log.addHandler(con_hand)

# регистратор для декоратора
deco_log = logging.getLogger("msg.deco")
deco_log.setLevel(logging.DEBUG)
deco_log.addHandler(deco_hand)
