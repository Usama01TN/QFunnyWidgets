# coding=utf-8
"""
Demo window for PufferCounterWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .puffercounter import PufferCounterWidget
except:
    from puffercounter import PufferCounterWidget


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
        self.setWindowTitle(self.tr('Puffer Counter demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 360)
        self.counter = PufferCounterWidget(maxLength=80, limitExceeded=self.onLimit)  # type: PufferCounterWidget
        self.post = QPushButton(self.tr('Post'))  # type: QPushButton
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(QLabel(self.tr('Compose a very short post (80 characters):')))
        layout.addWidget(self.counter, 1)
        layout.addWidget(self.post)
        self.setCentralWidget(wdg)

    @pyqtSlot(bool)
    def onLimit(self, over):
        """
        :param over: bool
        :return:
        """
        self.post.setEnabled(not over)
