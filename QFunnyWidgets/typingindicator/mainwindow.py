# coding=utf-8
"""
Demo window for TypingIndicatorWidget.
"""
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QCheckBox
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .typingindicator import TypingIndicatorWidget
except:
    from typingindicator import TypingIndicatorWidget


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
        self.setWindowTitle(self.tr('Typing Indicator demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 300)
        self.typing = TypingIndicatorWidget(name='Alex', autoCycle=True,
                                            stateChanged=self.onState)  # type: TypingIndicatorWidget
        self.typing.setMinimumHeight(110)
        row = QHBoxLayout()  # type: QHBoxLayout
        for label, st in (('Typing', TypingIndicatorWidget.Typing), ('Thinking', TypingIndicatorWidget.Thinking),
                          ('Deleting', TypingIndicatorWidget.Deleting), ('Sleeping', TypingIndicatorWidget.Sleeping)):
            b = QPushButton(self.tr(label))  # type: QPushButton
            b.clicked.connect(lambda _=False, s=st: (self.auto.setChecked(False), self.typing.setState(s)))
            row.addWidget(b)
        self.auto = QCheckBox(self.tr('Auto (realistic human)'))  # type: QCheckBox
        self.auto.setChecked(True)
        self.auto.toggled.connect(self.typing.setAutoCycle)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.typing, 1)
        layout.addLayout(row)
        layout.addWidget(self.auto)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onState(self, state):
        """
        :param state: int
        :return:
        """
        print('State: {}'.format(TypingIndicatorWidget.States(state).name))
