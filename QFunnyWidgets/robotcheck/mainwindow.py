# coding=utf-8
"""
Demo window for RobotCheckWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QSlider
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .robotcheck import RobotCheckWidget
except:
    from robotcheck import RobotCheckWidget


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
        self.setWindowTitle(self.tr('Robot Check demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(480, 360)
        self.check = RobotCheckWidget(verified=self.onVerified, failed=self.onFailed)  # type: RobotCheckWidget
        self.submit = QPushButton(self.tr('Create account'))  # type: QPushButton
        self.submit.setEnabled(False)
        reset = QPushButton(self.tr('Reset'))  # type: QPushButton
        reset.clicked.connect(self.check.reset)
        reset.clicked.connect(lambda: self.submit.setEnabled(False))
        fail = QSlider(Qt.Horizontal)  # type: QSlider
        fail.setRange(0, 100)
        fail.valueChanged.connect(lambda v: self.check.setFailChance(v / 100.0))
        row = QHBoxLayout()  # type: QHBoxLayout
        row.addWidget(QLabel(self.tr('Suspicion level')))
        row.addWidget(fail, 1)
        row.addWidget(reset)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.check, 1)
        layout.addWidget(self.submit)
        layout.addLayout(row)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onVerified(self):
        """
        :return:
        """
        self.submit.setEnabled(True)

    @pyqtSlot()
    def onFailed(self):
        """
        :return:
        """
        self.submit.setEnabled(False)
