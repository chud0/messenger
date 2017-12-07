#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QGridLayout, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QApplication, QDesktopWidget, QLineEdit, QTextEdit, QListWidget, QListView, QStackedWidget, QStackedLayout, QInputDialog)
from PyQt5.QtCore import QCoreApplication, pyqtSlot, QThread, pyqtSignal, QModelIndex, QItemSelectionModel
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
import bd_client_app
import client
import logging
import log_config
import time
import sys

mesg_con_log = logging.getLogger("msg.cons")


class ClientThreads(QThread):
    print_signal = pyqtSignal(tuple)
    # client это экземпляр класса Client из client.py

    def __init__(self, client, client_gui_ekz):
        QThread.__init__(self)
        self.client = client
        self.client_gui_ekz = client_gui_ekz

    def run(self):
        # print_queue = client.print_que
        while True:
            to_print = self.client.print_queue.get()
            self.print_signal.emit(to_print)
            if to_print[1] == "SYSTEM":  # ответ сервера в очередь
                self.client_gui_ekz.service_msg_deq.append(to_print[0])


class ClientGui(QWidget):

    def __init__(self):
        self.service_msg_deq = []  # очередь сервисных сообщений, очищать!
        self.icon_user = QIcon("user.svg")
        self.icon_new_msg = QIcon("message.svg")
        super().__init__()

        self.get_login_dialog()

    def initUI(self):

        # Кнопки: добавить/удалить контакты в контакт лист
        self.button_add_contact = QPushButton('add', self)
        self.button_add_contact.clicked.connect(self.add_contact)
        self.button_del_contact = QPushButton('del', self)
        self.button_del_contact.clicked.connect(self.del_contact)
        self.button_settings = QPushButton('men', self)
        self.button_settings.setEnabled(False)  # не работает
        self.button_connect = QPushButton('conn', self)
        self.button_connect.setEnabled(False)  # не работает

        self.box_button = QHBoxLayout()
        self.box_button.addWidget(self.button_add_contact)
        self.box_button.addWidget(self.button_del_contact)
        self.box_button.addWidget(self.button_settings)
        self.box_button.addWidget(self.button_connect)

        # создаю модель для листа контактов, подключаю отображение
        cl = bd_client_app.BDContacts().get_contacts()
        self.model_cl = QStandardItemModel()
        for user in cl:
            row = QStandardItem(self.icon_user, user)
            self.model_cl.appendRow(row)

        self.contact_list = QListView()
        self.contact_list.setModel(self.model_cl)
        self.contact_list.setSelectionMode(QListView.SingleSelection)
        self.contact_list.setEditTriggers(QListView.NoEditTriggers)
        self.contact_list.clicked.connect(self.select_conlist)

        # строка и кнопка отправки сообщений
        qButton = QPushButton('>>', self)
        qButton.clicked.connect(self.send_click)
        self.sendBox = QLineEdit(self)
        self.sendBox.returnPressed.connect(self.send_click)

        self.messageBox = QStackedWidget()
        # два словаря, в первом: логин ключ виджет значение, второй наоборот
        self.messageBox_dict_ctw = {}
        self.messageBox_dict_wtc = {}
        for user in cl:
            self.messageBox_dict_ctw[user] = QListWidget()
            self.messageBox_dict_wtc[self.messageBox_dict_ctw[user]] = user
            self.messageBox.addWidget(self.messageBox_dict_ctw[user])

        grid = QGridLayout()
        # строка, столбец, растянуть на строк, растянуть на столбцов
        grid.addWidget(self.contact_list, 0, 0, 2, 3)
        grid.addLayout(self.box_button, 2, 0)
        grid.addWidget(self.messageBox, 0, 3, 2, 3)
        grid.addWidget(self.sendBox, 2, 3, 1, 2)
        grid.addWidget(qButton, 2, 5)

        grid.setSpacing(5)
        grid.setColumnMinimumWidth(3, 200)
        grid.setColumnStretch(3, 10)
        self.setLayout(grid)

        self.resize(800, 300)
        self.center()
        self.setWindowTitle('Avocado')
        self.setWindowIcon(QIcon('icon.svg'))
        self.show()

    def initThreads(self):
        self.print_thread = ClientThreads(self.client, self)
        self.print_thread.print_signal.connect(self.add_message)
        self.print_thread.start()

    def get_login_dialog(self):

        text, ok = QInputDialog.getText(self, 'Login', 'Connect with login:')
        self.login_name = str(text)

        if ok:
            self.service_msg_deq.clear()  # жду свой ответ

            self.init_client()
            self.initThreads()

            # while not self.service_msg_deq:
            #     print(self.service_msg_deq)
            #     pass  # жду ответ
            # if self.service_msg_deq[0] is True:
            time.sleep(1)
            self.initUI()
            # else:
            #     self.exit()
        else:
            self.exit()

    def init_client(self):
        self.client = client.Client(self.login_name, "localhost", 7777)
        self.client.start_th_gui_client()

    def center(self):
        # центрирую окно
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @pyqtSlot()
    def send_click(self):
        text_to_send = self.sendBox.text()
        if text_to_send.rstrip():
            self.messageBox.currentWidget().addItem("<< " + text_to_send)
            self.client.inp_queue.put(text_to_send)
        self.sendBox.clear()

    @pyqtSlot(QModelIndex)
    def select_conlist(self, curr):
        self.messageBox.setCurrentIndex(curr.row())
        self.model_cl.itemFromIndex(curr).setIcon(self.icon_user)
        self.client.to_user = self.messageBox_dict_wtc[self.messageBox.currentWidget()]

    @pyqtSlot(tuple)
    def add_message(self, message):
        msg = message[0]
        from_u = message[1]

        try:
            client_widget = self.messageBox_dict_ctw[from_u]
        except KeyError:
            mesg_con_log.error("Message from user from not in contact list:")
            mesg_con_log.error("%s, %s" % (from_u, msg))
        else:
            client_widget.addItem(">> " + msg)
            message_from = self.model_cl.findItems(from_u)[0]
            if self.contact_list.currentIndex() != self.model_cl.indexFromItem(message_from):
                message_from.setIcon(self.icon_new_msg)

    @pyqtSlot()
    def del_contact(self):
        user = self.client.to_user
        self.client.inp_queue.put("del_contact " + user)
        self.messageBox.removeWidget(self.messageBox_dict_ctw[user])
        self.model_cl.takeRow(self.model_cl.indexFromItem(self.model_cl.findItems(user)[0]).row())

    @pyqtSlot()
    def add_contact(self):
        user = self.sendBox.text()
        self.service_msg_deq.clear()  # жду свой ответ
        self.client.inp_queue.put("add_contact " + user)

        while not self.service_msg_deq:
            pass  # жду ответ

        if self.service_msg_deq[0] is True:
            row = QStandardItem(self.icon_user, user)
            self.model_cl.appendRow(row)

            self.messageBox_dict_ctw[user] = QListWidget()
            self.messageBox_dict_wtc[self.messageBox_dict_ctw[user]] = user
            self.messageBox.addWidget(self.messageBox_dict_ctw[user])
        else:
            pass

        self.sendBox.clear()


def main():
    app = QApplication(sys.argv)
    ex = ClientGui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
