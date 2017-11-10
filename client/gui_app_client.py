#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGridLayout, QWidget, QPushButton, QApplication, QDesktopWidget, QLineEdit, QTextEdit, QListWidget, QStackedWidget
from PyQt5.QtCore import QCoreApplication, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
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
        super().__init__()
        self.init_client()
        # time.sleep(0.1)
        self.initUI()
        self.initThreads()


    def initUI(self):
        qButton = QPushButton('Send', self)
        qButton.clicked.connect(self.send_click)

        self.sendBox = QLineEdit(self)
        self.sendBox.returnPressed.connect(self.send_click)

        self.contact_list = QListWidget()
        cl = bd_client_app.BDContacts().get_contacts()
        self.contact_list.addItems(cl)
        self.contact_list.currentRowChanged.connect(self.select_conlist)

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

        self.contact_list.setCurrentRow(0)

        # строка, столбец, растянуть на строк, растянуть на столбцов
        grid.addWidget(self.contact_list, 0, 0, 2, 1)
        grid.addWidget(self.messageBox, 0, 1, 2, 3)
        grid.addWidget(self.sendBox, 3, 1, 1, 2)
        grid.addWidget(qButton, 3, 3)

        grid.setSpacing(10)
        grid.setColumnMinimumWidth(1, 200)
        # grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 10)
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

    @pyqtSlot()
    def select_conlist(self):
        self.messageBox.setCurrentIndex(self.contact_list.currentRow())
        self.client.to_user = self.messageBox_dict_wtc[self.messageBox.currentWidget()]

    @pyqtSlot(tuple)
    def add_message(self, message):
        msg = message[0]
        from_u = message[1]
        # self.messageBox.currentWidget().addItem(from_u + ">> " + msg)
        try:
            client_widget = self.messageBox_dict_ctw[from_u]
        except KeyError:
            mesg_con_log.error("Message from user from not in contact list")
        else:
            client_widget.addItem(">> " + msg)



if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = ClientGui()
    sys.exit(app.exec_())
