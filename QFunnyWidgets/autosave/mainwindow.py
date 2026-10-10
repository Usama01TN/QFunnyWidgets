# coding=utf-8
"""
Demo window for AutosaveSquirrelWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPlainTextEdit, QSlider, QLabel
from ManyQt.QtCore import Qt, QTimer, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from random import random
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .autosave import AutosaveSquirrelWidget
except:
    from autosave import AutosaveSquirrelWidget


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
        self.setWindowTitle(self.tr('Autosave Squirrel demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 380)
        self.editor = QPlainTextEdit()  # type: QPlainTextEdit
        self.editor.setPlaceholderText(self.tr('Type something. Stop typing. Watch the squirrel.'))
        self.squirrel = AutosaveSquirrelWidget(autosaveDelay=1200, retryDelay=2500,
                                               saveRequested=self.onSave)  # type: AutosaveSquirrelWidget
        self.editor.textChanged.connect(self.squirrel.markDirty)
        self.fail = QSlider(Qt.Horizontal)  # type: QSlider
        self.fail.setRange(0, 100)
        self.fail.setValue(20)
        row = QHBoxLayout()  # type: QHBoxLayout
        row.addWidget(QLabel(self.tr('Server flakiness')))
        row.addWidget(self.fail, 1)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.editor, 1)
        layout.addWidget(self.squirrel)
        layout.addLayout(row)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onSave(self):
        """
        Pretend to talk to a server.
        :return:
        """
        ok = random() * 100 >= self.fail.value()  # type: bool
        QTimer.singleShot(1300, lambda: self.squirrel.saveFinished(ok))
