# coding=utf-8
"""
Demo window for SnailStepperWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .snailstepper import SnailStepperWidget
except:
    from snailstepper import SnailStepperWidget


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
        self.setWindowTitle(self.tr('Snail Stepper demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(640, 300)
        self.stepper = SnailStepperWidget(arrived=self.onArrived)  # type: SnailStepperWidget
        self.info = QLabel(self.tr('Click Next a few times quickly. The snail will not be rushed.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        back = QPushButton(self.tr('Back'))  # type: QPushButton
        back.clicked.connect(self.stepper.previous)
        nxt = QPushButton(self.tr('Next'))  # type: QPushButton
        nxt.clicked.connect(self.stepper.next)
        row = QHBoxLayout()  # type: QHBoxLayout
        row.addWidget(back)
        row.addStretch(1)
        row.addWidget(nxt)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.stepper, 1)
        layout.addWidget(self.info)
        layout.addLayout(row)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onArrived(self, index):
        """
        :param index: int
        :return:
        """
        self.info.setText(self.tr('The snail reached step {}.').format(index + 1))
