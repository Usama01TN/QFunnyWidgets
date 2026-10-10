# coding=utf-8
"""
Demo window for PigeonToast.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QListWidget, QLineEdit
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from random import choice
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .pigeontoast import PigeonToast
except:
    from pigeontoast import PigeonToast

SAMPLES = ['File saved successfully.', 'Your build passed! (Somehow.)', '3 new comments on your pull request.',
           'Meeting moved to 4 pm. Again.', 'Backup completed. Your data is safe-ish.']  # type: list[str]


class MainWindow(QMainWindow):
    """
    MainWindow class.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr('Pigeon Toast demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(720, 460)
        wdg = QWidget()  # type: QWidget
        content = QListWidget()  # type: QListWidget
        for i in range(12):
            content.addItem(self.tr('Some very important document #{}').format(i + 1))
        self.edit = QLineEdit()  # type: QLineEdit
        self.edit.setPlaceholderText(self.tr('Type a message for the pigeon...'))
        send = QPushButton(self.tr('Send pigeon'))  # type: QPushButton
        send.clicked.connect(self.onSend)
        self.edit.returnPressed.connect(self.onSend)
        flock = QPushButton(self.tr('Send 3'))  # type: QPushButton
        flock.clicked.connect(self.onFlock)
        row = QHBoxLayout()  # type: QHBoxLayout
        row.addWidget(self.edit, 1)
        row.addWidget(send)
        row.addWidget(flock)
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(content, 1)
        layout.addLayout(row)
        self.setCentralWidget(wdg)
        # The overlay covers the central widget and follows its size.
        self.toast = PigeonToast(wdg, duration=2600, messageFinished=self.onDelivered)  # type: PigeonToast
        self.toast.showMessage(self.tr('Welcome! This message was delivered by pigeon.'))

    @pyqtSlot()
    def onSend(self):
        """
        :return:
        """
        self.toast.showMessage(self.edit.text() or choice(SAMPLES))
        self.edit.clear()

    @pyqtSlot()
    def onFlock(self):
        """
        :return:
        """
        for _ in range(3):
            self.toast.showMessage(choice(SAMPLES), 1500)

    @pyqtSlot('QString')
    def onDelivered(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        print('Delivered: {}'.format(text))
