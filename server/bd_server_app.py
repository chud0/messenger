# coding: UTF-8

from sqlalchemy import create_engine, and_
from sqlalchemy import Table, Column, Integer, Numeric, Float, String, MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import exc
# from sqlalchemy.orm import relationship

engine = create_engine('sqlite:///server.sqlite', echo=False)
Session = sessionmaker(bind=engine)

# Функция declarative_base создаёт базовый класс для декларативной работы
Base = declarative_base()


# Классы для работы с данными БД
class Users(Base):
    __tablename__ = "Users"
    UserID = Column(Integer, primary_key=True)
    UserLog = Column(String, unique=True)
    UserPswd = Column(String)
    UserDiscr = Column(String)

    def __init__(self, login, password, description):
        self.UserLog = login
        self.UserPswd = password
        self.UserDiscr = description

    def __repr__(self):
        return "<User: %s>" % self.UserLog


class UsersHstr(Base):
    __tablename__ = "UsersHistory"
    Time = Column(Float, primary_key=True)
    UserID = Column(Integer, ForeignKey('Users.UserID'))
    IP = Column(String)

    def __init__(self, time_tr, usr_id, ip):
        self.Time = time_tr
        self.UserID = usr_id
        self.IP = ip

    def __repr__(self):
        return "<User %s, time %s, ip %s>" % (self.UserID, self.Time, self.IP)


class ContactList(Base):
    __tablename__ = "ContactList"
    UserID = Column(Integer, ForeignKey('Users.UserID'), primary_key=True)
    ClientID = Column(Integer, ForeignKey('Users.UserID'), primary_key=True)

    def __init__(self, user_id, clnt_id):
        self.UserID = user_id
        self.ClientID = clnt_id

    def __repr__(self):
        return "<User %s in contact list user %s>" % (self.ClientID, self.UserID)


Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)  # create DB

# Создаём сессию
session = Session()


# Классы для работы с БД необходимые для работы методы
class BDUsers:
    """
    Class for work with "Users" table
    """
    def __init__(self):
        self.session = Session

    def add_user(self, login, password, description=""):
        session = self.session()
        session.add(Users(login, password, description))
        session.commit()

    def remove_user(self, login):
        # not for use
        session = self.session()
        try:
            log = self.find_user(login, session)()
        except exc.NoResultFound:
            return False
        else:
            session.delete(log)
            return True
        finally:
            session.commit()

    def find_user(self, login, session):
        # find user on login
        return session.query(Users).filter(Users.UserLog == login).one

    def find_user_id(self, us_id, session):
        return session.query(Users).filter(Users.UserID == us_id).one

    def all_users(self):
        session = self.session()
        a_users = session.query(Users.UserLog).all()
        return [usr[0] for usr in a_users]

    def check_user(self, login):
        if login in self.all_users():
            return True
        else:
            return False


class BDCList:
    """
    Class for work wit contact list
    """
    def __init__(self):
        self.session = Session

    def add_client(self, user, client):
        # add client (login) to user (login) contact list
        session = self.session()
        try:
            us = BDUsers().find_user(user, session)()
        except exc.NoResultFound:
            return False
        try:
            cl = BDUsers().find_user(client, session)()
        except exc.NoResultFound:
            return False
        session.add(ContactList(us.UserID, cl.UserID))
        session.commit()
        return True

    def remove_client(self, user, client):
        # remove client on user contact list
        session = self.session()
        try:
            us = BDUsers().find_user(user, session)()
        except exc.NoResultFound:
            return False
        try:
            cl = BDUsers().find_user(client, session)()
        except exc.NoResultFound:
            return False
        entry = session.query(
                ContactList).filter(and_(ContactList.UserID == us.UserID), (ContactList.ClientID == cl.UserID)).one()
        session.delete(entry)
        session.commit()
        return True

    def get_list(self, user):
        session = self.session()
        try:
            us = BDUsers().find_user(user, session)()
        except exc.NoResultFound:
            return False
        cl_list_id = session.query(ContactList).filter(ContactList.UserID == us.UserID).all()
        cl_list = [BDUsers().find_user_id(client.ClientID, session)().UserLog for client in cl_list_id]
        session.commit()
        return cl_list


class BDHistory:
    def __init__(self):
        self.session = Session

    def add_entry(self, time_tr, user, ip):
        session = self.session()
        try:
            user_id = BDUsers().find_user(user, session)().UserID
        except exc.NoResultFound:
            return False
        session.add(UsersHstr(time_tr, user_id, ip))
        session.commit()
        return True

    def get_history(self, user):
        session = self.session()
        try:
            user_id = BDUsers().find_user(user, session)().UserID
        except exc.NoResultFound:
            return False
        history = session.query(UsersHstr).filter(UsersHstr.UserID == user_id).all()
        session.commit()
        return history

    def get_history_all(self):
        session = self.session()
        history = session.query(UsersHstr).all()
        session.commit()
        return history
