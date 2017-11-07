# coding: UTF-8

from sqlalchemy import create_engine, and_
from sqlalchemy import Table, Column, Integer, Numeric, Float, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import exc

engine = create_engine('sqlite:///client.sqlite', echo=False)

Session = sessionmaker(bind=engine)
# Функция declarative_base создаёт базовый класс для декларативной работы
Base = declarative_base()

# Классы для работы с данными БД
class Contacts(Base):
    """
    Класс - отображение контактов в базе.
    ID - id записи
    UserLog - логин юзера
    UserDiscr - описание юзера (не используется)
    """
    __tablename__ = "contacts"
    ID = Column(Integer, primary_key=True, autoincrement=True)
    UserLog = Column(String, unique=True)
    UserDiscr = Column(String)

    def __init__(self, login, description=""):
        self.UserLog = login
        self.UserDiscr = description

    def __repr__(self):
        return "<User: %s>" % self.UserLog

class MsgHistory(Base):
    """
    Класс - отображение истории сообщений в базе.
    time - время получения сообщения
    client - логин юзера (пока для исходящих передаю self)
    incoming_msg - флаг входящего сообщения. True - входящее False - исходящее
    """
    __tablename__ = "msg_history"
    time = Column(Float, primary_key=True)
    client = Column(String, primary_key=True)
    message = Column(String)
    incoming_msg = Column(Boolean)  # входящее/исходящее - True/False

    def __init__(self, time, client, message, incoming_msg):
        self.time = time
        self.client = client
        self.message = message
        self.incoming_msg = incoming_msg

        def __repr__(self):
            return "<Msg('%s','%s','%s')>" % (self.time, self.client_id, self.message)


Base.metadata.create_all(engine)  # create DB


class BDMsgHistory:
    """
    Класс истории сообщений.
    save_history - записывет сообщение в базу
    get_history (в разработке) -  достает сообщения из базы
    """
    def __init__(self):
        self.Session = Session

    def save_history(self, time, client, message, incoming_msg=True):
        session = self.Session()
        session.add(MsgHistory(time, client, message, incoming_msg))
        session.commit()

class BDContacts:
    """
    Класс работы с контакт листом клиента.
    add_contact - добавляет контакт в базу
    remove_contact - удаляет контакт
    remove_contacts - удаляет все контакты
    update_contacts - обнавляет контакт лист по полученному списку
    """
    def __init__(self):
        self.session = Session

    def add_contact(self, contact_login):
        session = self.session()
        session.add(Contacts(contact_login))
        session.commit()
        return True

    def remove_contact(self, contact_login):
        session = self.session()
        try:
            us = session.query(Contacts).filter(Contacts.UserLog==contact_login).one()
        except exc.NoResultFound:
            return False
        else:
            session.delete(us)
            session.commit()
            return True

    def remove_contacts(self):
        session = self.session()
        all_cont = session.query(Contacts).all()
        for cont in all_cont:
            session.delete(cont)
        session.commit()
        return True

    def update_contacts(self, user_list):
        self.remove_contacts()
        for user in user_list:
            self.add_contact(user)
        return True
