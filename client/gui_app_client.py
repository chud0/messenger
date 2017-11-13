#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QWidget, QPushButton, QApplication, QDesktopWidget, QLineEdit, QTextEdit, QListWidget, QListView, QStackedWidget
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
    def __init__(self, client):
        QThread.__init__(self)
        self.client = client

    def run(self):
        # print_queue = client.print_que
        while True:
            to_print = self.client.print_queue.get()
            self.print_signal.emit(to_print)


class ClientGui(QWidget):

    def __init__(self):
        self.icon_user = QIcon("user.svg")
        self.icon_new_msg = QIcon("message.svg")
        super().__init__()
        self.init_client()
        # time.sleep(0.1)
        self.initUI()
        self.initThreads()


    def initUI(self):
        qButton = QPushButton('Send', self)
        qButton.clicked.connect(self.send_click)

        self.button_add_contact = QPushButton('add', self)
        self.button_del_contact = QPushButton('del', self)
        self.button_del_contact.setEnabled(False)
        self.line_add_contact = QLineEdit(self)

        self.sendBox = QLineEdit(self)
        self.sendBox.returnPressed.connect(self.send_click)

        cl = bd_client_app.BDContacts().get_contacts()

        # создаю модель для листа контактов:
        self.model_cl = QStandardItemModel()
        for client in cl:
            row = QStandardItem(self.icon_user, client)
            self.model_cl.appendRow(row)

        self.contact_list = QListView()
        self.contact_list.setModel(self.model_cl)
        self.contact_list.setSelectionMode(QListView.SingleSelection)
        self.contact_list.setEditTriggers(QListView.NoEditTriggers)
        self.contact_list.clicked.connect(self.select_conlist)

        grid = QGridLayout()

        self.messageBox = QStackedWidget()
        # два словаря, в первом: логин ключ виджет значение, второй наоборот
        self.messageBox_dict_ctw = {}
        self.messageBox_dict_wtc = {}
        self.icon_user = QIcon('user.svg')
        for client in cl:
            self.messageBox_dict_ctw[client] = QListWidget()
            self.messageBox_dict_wtc[self.messageBox_dict_ctw[client]] = client
            self.messageBox.addWidget(self.messageBox_dict_ctw[client])

        self.box_contact_action = QHBoxLayout()
        self.box_contact_action.addWidget(self.line_add_contact, 10)
        self.box_contact_action.addWidget(self.button_add_contact, 0)
        self.box_contact_action.addWidget(self.button_del_contact, 0)

        # строка, столбец, растянуть на строк, растянуть на столбцов
        grid.addLayout(self.box_contact_action, 0, 0)
        grid.addWidget(self.contact_list, 1, 0, 2, 3)
        grid.addWidget(self.messageBox, 0, 3, 2, 3)
        grid.addWidget(self.sendBox, 2, 3, 1, 2)
        grid.addWidget(qButton, 2, 5)

        grid.setSpacing(5)
        # grid.setColumnMinimumWidth(0, 70)
        grid.setColumnMinimumWidth(3, 200)
        # grid.setColumnStretch(0, 1)
        grid.setColumnStretch(3, 10)
        self.setLayout(grid)

        self.resize(500, 300)
        self.center()
        self.setWindowTitle('Avocado')
        self.setWindowIcon(QIcon('icon.svg'))
        self.show()

    def initThreads(self):
        self.print_thread = ClientThreads(self.client)
        self.print_thread.print_signal.connect(self.add_message)
        self.print_thread.start()

    def init_client(self):
        self.client = client.Client("usr1", "localhost", 7777)
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
            mesg_con_log.error("Message from user from not in contact list")
        else:
            client_widget.addItem(">> " + msg)
            message_from = self.model_cl.findItems(from_u)[0]
            if self.contact_list.currentIndex() != self.model_cl.indexFromItem(message_from):
                message_from.setIcon(self.icon_new_msg)



if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = ClientGui()
    sys.exit(app.exec_())
