# coding=utf-8
"""
Demo window for PasswordJudgeWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .passwordjudge import PasswordJudgeWidget
except:
    from passwordjudge import PasswordJudgeWidget


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
        self.setWindowTitle(self.tr('Password Judge demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 340)
        title = QLabel(self.tr('Create your account'))  # type: QLabel
        f = title.font()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        self.judge = PasswordJudgeWidget(minLength=8, strengthChanged=self.onStrength)  # type: PasswordJudgeWidget
        self.info = QLabel(self.tr('Try "password", then something long with symbols. Then press Show.'))  # type: QLabel
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.setContentsMargins(24, 20, 24, 20)
        layout.addWidget(title)
        layout.addWidget(self.judge, 1)
        layout.addWidget(self.info)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onStrength(self, strength):
        """
        :param strength: int
        :return:
        """
        print(self.tr('Strength: {}').format(strength))
