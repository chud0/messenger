# coding: UTF-8

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, MetaData
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///client.sqlite', echo=False)

# Подготовим "запрос" на создание таблицы users внутри каталога MetaData
metadata = MetaData()
# первым пусть будет сам клиент
client_table = Table(
    'contacts', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('login', String(64)),
    Column('description', String(64)),
)
# сообщения от id==1 - исходящие, позже, пока строками
message_history_table = Table(
    'msg_history', metadata,
    Column('time', Float, primary_key=True),
    Column('client', String, primary_key=True),
    Column('message', String),
    Column('incoming_msg', Boolean)  # входящее/исходящее - True/False
)
# Выполним запрос CREATE TABLE
metadata.create_all(engine)


# Создадим класс для отображения юзера из списка контактов
class User:
    def __init__(self, login, description):
        self.login = login
        self.description = description

    def __repr__(self):
        return "<User('%s','%s')>" % (self.login, self.description)


class MsgHistory:
    def __init__(self, time, client, message, incoming_msg):
        self.time = time
        self.client = client
        self.message = message
        self.incoming_msg = incoming_msg

    def __repr__(self):
        return "<Msg('%s','%s','%s')>" % (self.time, self.client_id, self.message)


# Выполним связывание таблицы и класса-отображения
m_u = mapper(User, client_table)
m_h = mapper(MsgHistory, message_history_table)

Session = sessionmaker(bind=engine)


class BDMsgHistory():
    """
    Класс истории сообщений.
    Метод save_history записывет сообщение в базу.
    Метод get_history (в разработке) достает сообщения из базы.
    """
    def __init__(self):
        self.Session = Session

    def save_history(self, time, client, message, incoming_msg=True):
        session = self.Session()
        session.add(MsgHistory(time, client, message, incoming_msg))
        session.commit()
