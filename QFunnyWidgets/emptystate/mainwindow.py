# coding=utf-8
"""
Demo window for EmptyStateWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QStackedWidget, QListWidget, QPushButton
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .emptystate import EmptyStateWidget
except:
    from emptystate import EmptyStateWidget


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
        self.setWindowTitle(self.tr('Empty State demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 420)
        self.empty = EmptyStateWidget(title='No tasks yet', actionText='Add a task',
                                      actionClicked=self.onAdd)  # type: EmptyStateWidget
        self.list = QListWidget()  # type: QListWidget
        self.stack = QStackedWidget()  # type: QStackedWidget
        self.stack.addWidget(self.empty)
        self.stack.addWidget(self.list)
        clear = QPushButton(self.tr('Clear list'))  # type: QPushButton
        clear.clicked.connect(self.onClear)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.stack, 1)
        layout.addWidget(clear)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onAdd(self):
        """
        :return:
        """
        self.list.addItem(self.tr('Task #{}: water the cactus').format(self.list.count() + 1))
        self.stack.setCurrentWidget(self.list)

    @pyqtSlot()
    def onClear(self):
        """
        :return:
        """
        self.list.clear()
        self.stack.setCurrentWidget(self.empty)
