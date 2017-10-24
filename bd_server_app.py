# coding: UTF-8

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, Float, MetaData

engine = create_engine('sqlite:///server.sqlite', echo=False)

# Подготовим "запрос" на создание таблицы users внутри каталога MetaData
metadata = MetaData()
client_table = Table('client', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('login', String(64)),
    Column('password', String(64)),
    Column('description', String(64)),
)

client_history_table = Table('client_history', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('client_id', Integer),
    Column('time', Float),
    Column('ip', String(64)),
)
# Выполним запрос CREATE TABLE
metadata.create_all(engine)
