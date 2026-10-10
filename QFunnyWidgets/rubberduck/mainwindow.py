# coding=utf-8
"""
Demo window for RubberDuckWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QPushButton
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .rubberduck import RubberDuckWidget
except:
    from rubberduck import RubberDuckWidget


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
        self.setWindowTitle(self.tr('Rubber Duck demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 460)
        self.duck = RubberDuckWidget(squeaked=self.onSqueak)  # type: RubberDuckWidget
        self.info = QLabel(self.tr('Click the duck, or describe your bug below.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        self.question = QLineEdit()  # type: QLineEdit
        self.question.setPlaceholderText(self.tr('My code works but I do not know why...'))
        ask = QPushButton(self.tr('Explain to duck'))  # type: QPushButton
        ask.clicked.connect(self.onAsk)
        self.question.returnPressed.connect(self.onAsk)
        row = QHBoxLayout()  # type: QHBoxLayout
        row.addWidget(self.question, 1)
        row.addWidget(ask)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.duck, 1)
        layout.addWidget(self.info)
        layout.addLayout(row)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onAsk(self):
        """
        :return:
        """
        self.duck.listen(self.question.text())
        self.question.clear()

    @pyqtSlot(int)
    def onSqueak(self, count):
        """
        :param count: int
        :return:
        """
        self.info.setText(self.tr('Squeaks: {}').format(count))
